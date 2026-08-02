"""
RAG Pipeline for Enterprise AI Knowledge Assistant.
The BRAIN that connects all modules together.

Phase 1 Upgrades:
- Semantic chunking (replaces fixed-size)
- Hybrid search BM25 + Vector (replaces pure vector)
- MMR diversity retrieval (removes duplicate chunks)
- BM25 index rebuilt after every document indexed
"""

import os
from typing import List, Dict, Any, Optional, Generator
from src.loaders.document_manager import DocumentManager
from src.chunking.chunker import TextChunker
from src.embeddings.embedding_model import EmbeddingModel
from src.vectorstore.vector_store import VectorStore
from src.llm.llm_client import LLMClient
from src.retrieval.retriever import Retriever
from src.retrieval.query_decomposer import QueryDecomposer
from src.prompts.prompt_template import PromptTemplates
from src.utils.logger import get_pipeline_logger
from src.evaluation.confidence_scorer import ConfidenceScorer
from src.evaluation.hallucination_detector import HallucinationDetector

logger = get_pipeline_logger()


class RAGPipeline:
    """
    Master pipeline that orchestrates the entire RAG system.

    TWO main flows:

    INDEXING FLOW:
    Documents -> DocumentManager -> TextChunker -> EmbeddingModel -> VectorStore

    QUERYING FLOW:
    Question -> EmbeddingModel -> HybridRetriever -> PromptTemplates -> LLMClient -> Answer
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 top_k: int = 5,
                 persist_dir: str = "data/vectorstore",
                 llm_model: str = "llama-3.1-8b-instant",
                 embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"):

        logger.info("Initializing RAG Pipeline...")

        self.doc_manager = DocumentManager()

        self.chunker = TextChunker(
            chunk_size    = chunk_size,
            chunk_overlap = chunk_overlap
        )

        self.embedding_model = EmbeddingModel(
            model_name = embed_model
        )

        self.vector_store = VectorStore(
            persist_directory = persist_dir,
            collection_name   = "knowledge_base"
        )

        self.llm = LLMClient(
            model_name  = os.getenv("LLM_MODEL", llm_model),
            temperature = 0.1,
            max_tokens  = 2048
        )

        # Cross-encoder re-ranking runs a local torch model per query — safe
        # on a full local dev machine, but risky on Render's free tier
        # (512MB RAM). Default ON locally, but respect USE_CROSS_ENCODER=false
        # as an explicit opt-out for constrained environments.
        use_cross_encoder = os.getenv("USE_CROSS_ENCODER", "true").lower() != "false"

        self.retriever = Retriever(
            embedding_model   = self.embedding_model,
            vector_store      = self.vector_store,
            top_k             = top_k,
            min_similarity    = 0.0,
            use_cross_encoder = use_cross_encoder
        )

        # Query decomposition: splits genuinely multi-part questions into
        # sub-questions retrieved separately. Costs one extra LLM call,
        # but ONLY for questions that look multi-part (cheap heuristic
        # gate skips simple questions entirely). Default ON; opt out via
        # env var same as cross-encoder if you want to save latency/cost.
        use_query_decomposition = os.getenv("USE_QUERY_DECOMPOSITION", "true").lower() != "false"
        self.use_query_decomposition = use_query_decomposition
        self.query_decomposer = QueryDecomposer(self.llm) if use_query_decomposition else None

        self.prompts = PromptTemplates()
        self.loaded_docs: List[str] = []

        self.confidence_scorer      = ConfidenceScorer()
        self.hallucination_detector = HallucinationDetector()

        # Build BM25 index from any existing documents
        self.retriever.build_bm25_index()

        logger.info("RAG Pipeline ready!")

    # ════════════════════════════════════════════════════════════
    # INDEXING FLOW
    # ════════════════════════════════════════════════════════════

    def index_file(self,
                   file_bytes: bytes,
                   filename: str) -> Dict[str, Any]:
        """Index an uploaded file into the vector store."""
        logger.info(f"Indexing file: {filename}")

        try:
            # Step 1: Load document
            documents = self.doc_manager.load_from_bytes(
                file_bytes, filename
            )

            if not documents:
                return {
                    "success":  False,
                    "filename": filename,
                    "error":    "No content extracted"
                }

            # Step 2: Semantic chunking
            # Documents have {content, metadata} format
            # Convert to format chunker expects
            chunks_input = [
                {
                    "text":     doc.get("content", ""),
                    "metadata": doc.get("metadata", {})
                }
                for doc in documents
            ]
            chunks = self.chunker.chunk_documents(chunks_input)

            if not chunks:
                return {
                    "success":  False,
                    "filename": filename,
                    "error":    "No chunks created"
                }

            # Step 3: Create embeddings
            logger.info(f"Embedding {len(chunks)} chunks...")
            texts      = [c["text"] for c in chunks]
            embeddings = self.embedding_model.embed_batch(texts)

            # Step 4: Store in VectorStore
            # Convert chunks to format vector store expects
            vs_chunks = [
                {
                    "content":  c["text"],
                    "metadata": {
                        **c.get("metadata", {}),
                        "source":      filename,
                        "chunk_index": c.get("chunk_index", i),
                    }
                }
                for i, c in enumerate(chunks)
            ]
            self.vector_store.add_documents(vs_chunks, embeddings)

            # Track loaded doc
            if filename not in self.loaded_docs:
                self.loaded_docs.append(filename)

            # Rebuild BM25 index for hybrid search
            self.retriever.build_bm25_index()

            result = {
                "success":     True,
                "filename":    filename,
                "pages":       len(documents),
                "chunks":      len(chunks),
                "total_words": sum(len(c["text"].split()) for c in chunks),
            }

            logger.info(f"Indexed {filename}: {len(chunks)} chunks")
            return result

        except Exception as e:
            logger.error(f"Failed to index {filename}: {str(e)}")
            return {
                "success":  False,
                "filename": filename,
                "error":    str(e)
            }

    def index_url(self, url: str) -> Dict[str, Any]:
        """Index content from a URL."""
        logger.info(f"Indexing URL: {url}")

        try:
            documents = self.doc_manager.load_url(url)

            if not documents:
                return {
                    "success": False,
                    "url":     url,
                    "error":   "No content found at URL"
                }

            chunks_input = [
                {
                    "text":     doc.get("content", ""),
                    "metadata": doc.get("metadata", {})
                }
                for doc in documents
            ]
            chunks = self.chunker.chunk_documents(chunks_input)
            texts  = [c["text"] for c in chunks]
            embeddings = self.embedding_model.embed_batch(texts)

            vs_chunks = [
                {
                    "content":  c["text"],
                    "metadata": {
                        **c.get("metadata", {}),
                        "source":      url,
                        "chunk_index": c.get("chunk_index", i),
                    }
                }
                for i, c in enumerate(chunks)
            ]
            self.vector_store.add_documents(vs_chunks, embeddings)

            if url not in self.loaded_docs:
                self.loaded_docs.append(url)

            # Rebuild BM25 index
            self.retriever.build_bm25_index()

            logger.info(f"Indexed URL: {url} ({len(chunks)} chunks)")
            return {
                "success": True,
                "url":     url,
                "chunks":  len(chunks),
            }

        except Exception as e:
            logger.error(f"Failed to index URL {url}: {str(e)}")
            return {
                "success": False,
                "url":     url,
                "error":   str(e)
            }

    # ════════════════════════════════════════════════════════════
    # QUERYING FLOW
    # ════════════════════════════════════════════════════════════

    def ask(self,
            question: str,
            chat_history: Optional[List[Dict]] = None,
            stream: bool = True
            ) -> Generator[str, None, None]:
        """Answer a question using RAG."""
        logger.info(f"Question: {question[:60]}...")

        try:
            # Check if docs loaded
            if self.vector_store.count() == 0:
                yield (
                    "No documents loaded yet!\n\n"
                    "Please upload documents using the sidebar first."
                )
                return

            # Retrieve relevant chunks (hybrid search + MMR)
            context = self.retriever.get_context_text(
                question, max_chars=4000
            )

            # Build prompt
            if not context:
                prompt = PromptTemplates.no_context_prompt(question)
            elif chat_history and len(chat_history) > 0:
                prompt = PromptTemplates.followup_prompt(
                    question, context, chat_history
                )
            elif len(self.loaded_docs) > 1:
                prompt = PromptTemplates.multi_doc_prompt(
                    question, context, self.loaded_docs
                )
            else:
                prompt = PromptTemplates.rag_prompt(
                    question, context
                )

            # Generate answer
            if stream:
                yield from self.llm.generate_stream(
                    prompt        = prompt,
                    system_prompt = PromptTemplates.SYSTEM_PROMPT
                )
            else:
                answer = self.llm.generate(
                    prompt        = prompt,
                    system_prompt = PromptTemplates.SYSTEM_PROMPT
                )
                yield answer

        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            yield f"Error: {str(e)}"

    def _retrieve_with_decomposition(self,
                                      question: str,
                                      max_chars: int = 4000
                                      ) -> tuple:
        """
        Retrieve chunks for a question, decomposing genuinely multi-part
        questions into sub-questions retrieved separately first (see
        QueryDecomposer for what qualifies as "multi-part").

        Single shared helper for ask_stream_with_evaluation() and
        ask_with_evaluation() so decomposition behavior can't drift
        out of sync between the streaming and non-streaming paths.

        Returns:
            (chunks, context_text) — same shape as calling
            retriever.retrieve() + retriever.get_context_text() directly,
            so callers don't need to know whether decomposition happened.
        """
        if not self.use_query_decomposition:
            chunks  = self.retriever.retrieve(question)
            context = self.retriever.get_context_text(question, max_chars=max_chars, chunks=chunks)
            return chunks, context

        sub_questions = self.query_decomposer.decompose(question)

        if len(sub_questions) == 1:
            chunks  = self.retriever.retrieve(question)
            context = self.retriever.get_context_text(question, max_chars=max_chars, chunks=chunks)
            return chunks, context

        # Multi-part: retrieve each sub-question separately, merge + dedupe
        # by chunk id (so a chunk relevant to multiple sub-questions isn't
        # duplicated in the context), preserving first-seen order.
        seen_ids = set()
        merged_chunks: List[Dict[str, Any]] = []
        for sub_q in sub_questions:
            for chunk in self.retriever.retrieve(sub_q):
                chunk_id = chunk.get("id")
                if chunk_id not in seen_ids:
                    seen_ids.add(chunk_id)
                    merged_chunks.append(chunk)

        context = self.retriever.get_context_text(
            question, max_chars=max_chars, chunks=merged_chunks
        )
        return merged_chunks, context

    def ask_stream_with_evaluation(self,
                                    question: str,
                                    chat_history: Optional[List[Dict]] = None
                                    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream the answer token-by-token (single LLM call), then yield ONE
        final evaluation event with confidence + hallucination scores.

        This replaces the old flow of (1) stream the answer, then (2) call
        the LLM a second time via ask_with_evaluation() just to re-derive
        scores. Confidence/hallucination scoring is pure heuristics over the
        retrieved chunks + final answer text (no LLM call), so it can be
        computed immediately after the stream finishes, in the SAME request.

        Yields:
            {"type": "token", "token": str}                      -- while streaming
            {"type": "eval", "sources", "confidence",
             "hallucination_check"}                               -- once, at the end
        """
        logger.info(f"Question (stream+eval): {question[:60]}...")
        history = chat_history or []

        if self.vector_store.count() == 0:
            yield {"type": "token", "token": (
                "No documents loaded yet!\n\n"
                "Please upload documents using the sidebar first."
            )}
            yield {
                "type": "eval",
                "sources": [],
                "confidence": {"score": 0, "label": "No Context", "percentage": "0%"},
                "hallucination_check": {"risk_level": "HIGH", "is_grounded": False},
            }
            return

        try:
            # Retrieve once — reused for both prompt context and scoring.
            # Transparently handles query decomposition for multi-part
            # questions (see _retrieve_with_decomposition).
            chunks, context = self._retrieve_with_decomposition(question, max_chars=4000)

            if not context:
                prompt = PromptTemplates.no_context_prompt(question)
            elif history:
                prompt = PromptTemplates.followup_prompt(question, context, history)
            elif len(self.loaded_docs) > 1:
                prompt = PromptTemplates.multi_doc_prompt(question, context, self.loaded_docs)
            else:
                prompt = PromptTemplates.rag_prompt(question, context)

            full_answer_parts: List[str] = []
            for token in self.llm.generate_stream(
                prompt=prompt, system_prompt=PromptTemplates.SYSTEM_PROMPT
            ):
                full_answer_parts.append(token)
                yield {"type": "token", "token": token}

            full_answer = "".join(full_answer_parts)

            confidence = self.confidence_scorer.score(
                question=question, answer=full_answer, retrieved_chunks=chunks
            )
            hallucination_check = self.hallucination_detector.detect(
                answer=full_answer, retrieved_chunks=chunks, question=question
            )
            sources = [
                {
                    "content": c.get("content", "")[:300],
                    "source": c.get("metadata", {}).get("source", "Unknown"),
                    "page": c.get("metadata", {}).get("page_number"),
                    "similarity": c.get("similarity"),
                    "relevance_label": c.get("relevance_label"),
                }
                for c in chunks
            ]

            yield {
                "type": "eval",
                "sources": sources,
                "confidence": confidence,
                "hallucination_check": hallucination_check,
            }

        except Exception as e:
            logger.error(f"Pipeline error (stream+eval): {str(e)}")
            yield {"type": "token", "token": f"Error: {str(e)}"}
            yield {
                "type": "eval",
                "sources": [],
                "confidence": {"score": 0, "label": "Error", "percentage": "0%"},
                "hallucination_check": {"risk_level": "HIGH", "is_grounded": False},
            }

    def ask_with_evaluation(self,
                             question: str,
                             chat_history: Optional[List[Dict]] = None
                             ) -> Dict[str, Any]:
        """
        Non-streaming: answer a question and return full evaluation metadata
        in one shot. Kept for callers that want a single blocking response
        (e.g. batch evaluation in Phase 3, or non-streaming API clients).

        Returns:
        Dict with answer, sources, confidence, hallucination_check
        """
        if self.vector_store.count() == 0:
            return {
                "answer":   "No documents loaded yet. Please upload documents first.",
                "sources":  [],
                "confidence":          {"score": 0, "label": "No Context", "percentage": "0%"},
                "hallucination_check": {"risk_level": "HIGH", "is_grounded": False},
            }

        # Retrieve chunks (transparently decomposes multi-part questions)
        chunks, context = self._retrieve_with_decomposition(question)

        # Build prompt
        history = chat_history or []
        if not context:
            prompt = PromptTemplates.no_context_prompt(question)
        elif history:
            prompt = PromptTemplates.followup_prompt(question, context, history)
        elif len(self.loaded_docs) > 1:
            prompt = PromptTemplates.multi_doc_prompt(question, context, self.loaded_docs)
        else:
            prompt = PromptTemplates.rag_prompt(question, context)

        # Generate full answer (non-streaming for evaluation)
        answer = self.llm.generate(
            prompt        = prompt,
            system_prompt = PromptTemplates.SYSTEM_PROMPT
        )

        # Score confidence
        confidence = self.confidence_scorer.score(
            question = question,
            answer   = answer,
            retrieved_chunks = chunks
        )

        # Detect hallucinations
        hallucination_check = self.hallucination_detector.detect(
            answer           = answer,
            retrieved_chunks = chunks,
            question         = question
        )

        # Format sources
        sources = [
            {
                "content":  c.get("content", "")[:300],
                "source":   c.get("metadata", {}).get("source", "Unknown"),
                "page":     c.get("metadata", {}).get("page_number"),
                "similarity": c.get("similarity"),
                "relevance_label": c.get("relevance_label"),
            }
            for c in chunks
        ]

        return {
            "answer":              answer,
            "sources":             sources,
            "confidence":          confidence,
            "hallucination_check": hallucination_check,
        }

    def summarize(self,
                  filename: str) -> Generator[str, None, None]:
        """Summarize a specific loaded document."""
        logger.info(f"Summarizing: {filename}")

        try:
            results = self.vector_store.search(
                query_embedding = self.embedding_model.embed_text(
                    "summary overview main points key findings"
                ),
                top_k = 10,
            )

            if not results:
                yield f"No content found for {filename}"
                return

            doc_text = "\n\n".join([r["content"] for r in results])
            prompt   = PromptTemplates.summary_prompt(
                doc_text, filename
            )
            yield from self.llm.generate_stream(prompt)

        except Exception as e:
            logger.error(f"Summary failed: {str(e)}")
            yield f"Summary error: {str(e)}"

    def get_sources(self,
                    question: str) -> List[Dict[str, Any]]:
        """Get source documents for a question."""
        return self.retriever.retrieve(question)

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        vs_stats = self.vector_store.get_stats()
        return {
            "loaded_documents": len(self.loaded_docs),
            "document_names":   self.loaded_docs,
            "total_chunks":     vs_stats.get("total_chunks", 0),
            "llm_model":        self.llm.model_name,
            "embed_model":      self.embedding_model.model_name,
            "llm_available":    self.llm.is_available(),
        }

    def clear_knowledge_base(self) -> bool:
        """Clear all stored documents."""
        self.vector_store.clear()
        self.loaded_docs = []
        self.retriever._bm25_index  = None
        self.retriever._bm25_corpus = []
        self.retriever._bm25_docs   = []
        logger.info("Knowledge base cleared")
        return True

    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Delete a single document from the knowledge base: removes its
        chunks from the vector store, drops it from loaded_docs, and
        rebuilds the BM25 index so hybrid search stays in sync (otherwise
        the deleted doc's terms would still be searchable/retrievable via
        the stale BM25 index even after the vector store forgot it).

        Args:
            filename: The exact 'source' value the document was indexed
                      under (matches what /api/documents lists).

        Returns:
            {"success": bool, "filename": str, "chunks_deleted": int}
        """
        deleted_count = self.vector_store.delete_by_source(filename)

        if deleted_count == 0:
            logger.warning(f"delete_document: '{filename}' not found in vector store")
            return {"success": False, "filename": filename, "chunks_deleted": 0}

        if filename in self.loaded_docs:
            self.loaded_docs.remove(filename)

        # Rebuild BM25 from whatever remains (empty is fine — build_bm25_index
        # already handles the zero-documents case with a warning, not a crash)
        self.retriever.build_bm25_index()

        logger.info(f"Deleted document '{filename}' ({deleted_count} chunks)")
        return {"success": True, "filename": filename, "chunks_deleted": deleted_count}

    def check_system(self) -> Dict[str, bool]:
        """Check all system components."""
        return {
            "llm":         self.llm.is_available(),
            "embeddings":  self.embedding_model.is_available(),
            "vector_store": self.vector_store.count() > 0,
            "docs_loaded": len(self.loaded_docs) > 0,
        }