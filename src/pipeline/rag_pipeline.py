"""
RAG Pipeline for Enterprise AI Knowledge Assistant.
The BRAIN that connects all modules together.

Flow:
Documents → Load → Chunk → Embed → Store
Question  → Embed → Retrieve → Prompt → LLM → Answer
"""

from typing import List, Dict, Any, Optional, Generator
from src.loaders.document_manager import DocumentManager
from src.chunking.chunker import TextChunker
from src.embeddings.embedding_model import EmbeddingModel
from src.vectorstore.vector_store import VectorStore
from src.llm.llm_client import LLMClient
from src.retrieval.retriever import Retriever
from src.prompts.prompt_template import PromptTemplates
from src.utils.logger import get_pipeline_logger

logger = get_pipeline_logger()


class RAGPipeline:
    """
    Master pipeline that orchestrates the entire RAG system.

    TWO main flows:

    ── INDEXING FLOW ──────────────────────────────────────────
    Documents
        ↓ DocumentManager  (load files/URLs)
        ↓ TextChunker      (split into pieces)
        ↓ EmbeddingModel   (convert to vectors)
        ↓ VectorStore      (save to ChromaDB)
    Ready to answer! ✅

    ── QUERYING FLOW ──────────────────────────────────────────
    Question
        ↓ EmbeddingModel   (convert to vector)
        ↓ Retriever        (find similar chunks)
        ↓ PromptTemplates  (build smart prompt)
        ↓ LLMClient        (generate answer)
    Answer! ✅
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 top_k: int = 5,
                 persist_dir: str = "data/vectorstore",
                 llm_model: str = "llama3.2:3b",
                 embed_model: str = "nomic-embed-text",
                 base_url: str = "http://localhost:11434"):
        """Initialize all pipeline components."""

        logger.info("🚀 Initializing RAG Pipeline...")

        # ── Initialize all components ────────────────────────────
        self.doc_manager = DocumentManager()

        self.chunker = TextChunker(
            chunk_size    = chunk_size,
            chunk_overlap = chunk_overlap
        )

        self.embedding_model = EmbeddingModel(
            model_name = embed_model,
            base_url   = base_url
        )

        self.vector_store = VectorStore(
            persist_directory = persist_dir,
            collection_name   = "knowledge_base"
        )

        self.llm = LLMClient(
            model_name  = llm_model,
            base_url    = base_url,
            temperature = 0.1,
            max_tokens  = 2048
        )

        self.retriever = Retriever(
            embedding_model = self.embedding_model,
            vector_store    = self.vector_store,
            top_k           = top_k,
            min_similarity  = 0.3
        )

        self.prompts = PromptTemplates()

        # ── Track loaded documents ───────────────────────────────
        self.loaded_docs: List[str] = []

        logger.info("✅ RAG Pipeline ready!")

    # ════════════════════════════════════════════════════════════
    #  INDEXING FLOW
    # ════════════════════════════════════════════════════════════

    def index_file(self,
                   file_bytes: bytes,
                   filename: str) -> Dict[str, Any]:
        """
        Index an uploaded file into the vector store.

        Args:
            file_bytes: Raw bytes from Streamlit upload
            filename:   Original filename

        Returns:
            Dict with indexing stats
        """
        logger.info(f"📄 Indexing file: {filename}")

        try:
            # ── Step 1: Load document ────────────────────────────
            documents = self.doc_manager.load_from_bytes(
                file_bytes, filename
            )

            if not documents:
                return {
                    "success":  False,
                    "filename": filename,
                    "error":    "No content extracted"
                }

            # ── Step 2: Split into chunks ────────────────────────
            chunks = self.chunker.split_documents(documents)
            chunk_stats = self.chunker.get_stats(chunks)

            # ── Step 3: Create embeddings ────────────────────────
            logger.info(
                f"Creating embeddings for "
                f"{len(chunks)} chunks..."
            )
            texts = [c["content"] for c in chunks]
            embeddings = self.embedding_model.embed_batch(texts)

            # ── Step 4: Store in VectorStore ─────────────────────
            stored = self.vector_store.add_documents(
                chunks, embeddings
            )

            # ── Track loaded doc ─────────────────────────────────
            if filename not in self.loaded_docs:
                self.loaded_docs.append(filename)

            result = {
                "success":    True,
                "filename":   filename,
                "pages":      len(documents),
                "chunks":     len(chunks),
                "stored":     stored,
                "avg_chunk":  chunk_stats.get(
                                  "avg_chunk_size", 0
                              ),
                "total_words": chunk_stats.get(
                                   "total_words", 0
                               ),
            }

            logger.info(
                f"✅ Indexed {filename}: "
                f"{stored} chunks stored"
            )
            return result

        except Exception as e:
            logger.error(
                f"Failed to index {filename}: {str(e)}"
            )
            return {
                "success":  False,
                "filename": filename,
                "error":    str(e)
            }

    def index_url(self, url: str) -> Dict[str, Any]:
        """
        Index content from a URL.

        Args:
            url: Website URL to scrape and index

        Returns:
            Dict with indexing stats
        """
        logger.info(f"🌐 Indexing URL: {url}")

        try:
            # ── Load URL content ─────────────────────────────────
            documents = self.doc_manager.load_url(url)

            if not documents:
                return {
                    "success": False,
                    "url":     url,
                    "error":   "No content found at URL"
                }

            # ── Chunk, embed, store ──────────────────────────────
            chunks     = self.chunker.split_documents(documents)
            texts      = [c["content"] for c in chunks]
            embeddings = self.embedding_model.embed_batch(texts)
            stored     = self.vector_store.add_documents(
                             chunks, embeddings
                         )

            if url not in self.loaded_docs:
                self.loaded_docs.append(url)

            logger.info(
                f"✅ Indexed URL: {url} "
                f"({stored} chunks)"
            )
            return {
                "success": True,
                "url":     url,
                "chunks":  len(chunks),
                "stored":  stored,
            }

        except Exception as e:
            logger.error(
                f"Failed to index URL {url}: {str(e)}"
            )
            return {
                "success": False,
                "url":     url,
                "error":   str(e)
            }

    # ════════════════════════════════════════════════════════════
    #  QUERYING FLOW
    # ════════════════════════════════════════════════════════════

    def ask(self,
            question: str,
            chat_history: Optional[List[Dict]] = None,
            stream: bool = True
            ) -> Generator[str, None, None]:
        """
        Answer a question using RAG.

        Args:
            question:     User's question
            chat_history: Previous Q&A for context
            stream:       Stream response word by word

        Yields:
            Answer text chunks
        """
        logger.info(f"❓ Question: {question[:60]}...")

        try:
            # ── Step 1: Check if docs loaded ─────────────────────
            if self.vector_store.is_empty():
                yield (
                    "⚠️ No documents loaded yet!\n\n"
                    "Please upload documents or add URLs "
                    "using the sidebar first."
                )
                return

            # ── Step 2: Retrieve relevant chunks ─────────────────
            context = self.retriever.get_context_text(
                question, max_chars=4000
            )

            # ── Step 3: Build prompt ──────────────────────────────
            if not context:
                prompt = PromptTemplates.no_context_prompt(
                    question
                )
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

            # ── Step 4: Generate answer ───────────────────────────
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
            yield f"❌ Error: {str(e)}"

    def summarize(self,
                  filename: str) -> Generator[str, None, None]:
        """
        Summarize a specific loaded document.

        Args:
            filename: Name of document to summarize

        Yields:
            Summary text chunks
        """
        logger.info(f"📋 Summarizing: {filename}")

        try:
            # ── Get chunks for this document ──────────────────────
            results = self.vector_store.search(
                query_embedding = self.embedding_model.embed_text(
                    "summary overview main points"
                ),
                top_k           = 10,
                filter_source   = filename
            )

            if not results:
                yield f"No content found for {filename}"
                return

            # ── Combine chunks ────────────────────────────────────
            doc_text = "\n\n".join(
                [r["content"] for r in results]
            )

            # ── Build summary prompt ──────────────────────────────
            prompt = PromptTemplates.summary_prompt(
                doc_text, filename
            )

            # ── Stream summary ────────────────────────────────────
            yield from self.llm.generate_stream(prompt)

        except Exception as e:
            logger.error(f"Summary failed: {str(e)}")
            yield f"❌ Summary error: {str(e)}"

    def get_sources(self,
                    question: str) -> List[Dict[str, Any]]:
        """
        Get source documents for a question
        without generating an answer.

        Used to show sources panel in UI.
        """
        return self.retriever.retrieve_with_scores(question)

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics for dashboard."""
        vs_stats = self.vector_store.get_stats()
        return {
            "loaded_documents": len(self.loaded_docs),
            "document_names":   self.loaded_docs,
            "total_chunks":     vs_stats.get(
                                    "total_chunks", 0
                                ),
            "llm_model":        self.llm.model_name,
            "embed_model":      self.embedding_model.model_name,
            "llm_available":    self.llm.is_available(),
        }

    def clear_knowledge_base(self) -> bool:
        """Clear all stored documents."""
        success = self.vector_store.clear()
        if success:
            self.loaded_docs = []
            logger.info("✅ Knowledge base cleared")
        return success

    def check_system(self) -> Dict[str, bool]:
        """
        Check all system components are working.
        Shows in UI dashboard.
        """
        return {
            "ollama_llm":       self.llm.is_available(),
            "ollama_embeddings":self.embedding_model.is_available(),
            "vector_store":     not self.vector_store.is_empty(),
            "docs_loaded":      len(self.loaded_docs) > 0,
        }