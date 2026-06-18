"""
Retriever for Enterprise AI Knowledge Assistant.
Finds most relevant document chunks for any question.
"""

from typing import List, Dict, Any, Optional
from src.embeddings.embedding_model import EmbeddingModel
from src.vectorstore.vector_store import VectorStore
from src.utils.logger import setup_logger

logger = setup_logger("Retriever")


class Retriever:
    """
    Finds most relevant chunks for a user question.

    How it works:
        1. Takes user question as text
        2. Converts question to embedding vector
        3. Searches VectorStore for similar chunks
        4. Returns top-k most relevant chunks

    Think of it like Google Search but for
    YOUR documents using AI understanding!
    """

    def __init__(self,
                 embedding_model: EmbeddingModel,
                 vector_store: VectorStore,
                 top_k: int = 5,
                 min_similarity: float = 0.3):
        """
        Args:
            embedding_model: Model to embed questions
            vector_store:    Database to search
            top_k:           Max results to return
            min_similarity:  Minimum relevance score
        """
        self.embedding_model = embedding_model
        self.vector_store    = vector_store
        self.top_k           = top_k
        self.min_similarity  = min_similarity

        logger.info(
            f"Retriever ready — "
            f"top_k={top_k}, "
            f"min_similarity={min_similarity}"
        )

    def retrieve(self,
                 question: str,
                 top_k: Optional[int] = None,
                 filter_source: Optional[str] = None
                 ) -> List[Dict[str, Any]]:
        """
        Find most relevant chunks for a question.

        Args:
            question:      User's question text
            top_k:         Override default top_k
            filter_source: Only search specific document

        Returns:
            List of relevant chunks with similarity scores
        """
        if not question or not question.strip():
            logger.warning("Empty question received")
            return []

        k = top_k or self.top_k

        # ── Check if vectorstore has documents ───────────────────
        if self.vector_store.is_empty():
            logger.warning("VectorStore is empty!")
            return []

        try:
            # ── Step 1: Embed the question ───────────────────────
            logger.info(f"Retrieving for: '{question[:50]}...'")
            question_embedding = self.embedding_model.embed_text(
                question
            )

            # ── Step 2: Search VectorStore ───────────────────────
            results = self.vector_store.search(
                query_embedding = question_embedding,
                top_k           = k,
                filter_source   = filter_source
            )

            # ── Step 3: Filter by minimum similarity ─────────────
            filtered = [
                r for r in results
                if r["similarity"] >= self.min_similarity
            ]

            if not filtered:
                logger.warning(
                    f"No chunks above similarity "
                    f"threshold {self.min_similarity}"
                )
                return results[:3]  # Return top 3 anyway

            logger.info(
                f"Retrieved {len(filtered)} relevant chunks "
                f"(similarity >= {self.min_similarity})"
            )
            return filtered

        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            raise

    def retrieve_with_scores(self,
                             question: str
                             ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks with detailed scoring info.
        Used for showing sources in the UI.
        """
        results = self.retrieve(question)

        # ── Add rank and score label ─────────────────────────────
        for i, result in enumerate(results):
            score = result["similarity"]
            result["rank"] = i + 1
            result["relevance_label"] = (
                "🟢 High"   if score >= 0.7 else
                "🟡 Medium" if score >= 0.5 else
                "🔴 Low"
            )

        return results

    def get_context_text(self,
                         question: str,
                         max_chars: int = 4000
                         ) -> str:
        """
        Get retrieved chunks as single context string.
        This gets passed to the LLM as context.

        Args:
            question:  User question
            max_chars: Max context length for LLM

        Returns:
            Formatted context string
        """
        chunks = self.retrieve(question)

        if not chunks:
            return ""

        # ── Format chunks with source info ───────────────────────
        context_parts = []
        total_chars   = 0

        for i, chunk in enumerate(chunks):
            source = chunk["metadata"].get("source", "Unknown")
            page   = chunk["metadata"].get("page_number", "")
            page_info = f" (Page {page})" if page else ""

            chunk_text = (
                f"[Source {i+1}: {source}{page_info}]\n"
                f"{chunk['content']}\n"
            )

            # Stop if context getting too long
            if total_chars + len(chunk_text) > max_chars:
                break

            context_parts.append(chunk_text)
            total_chars += len(chunk_text)

        context = "\n---\n".join(context_parts)
        logger.info(
            f"Context prepared: "
            f"{len(context)} chars from "
            f"{len(context_parts)} chunks"
        )
        return context