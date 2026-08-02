"""
Hybrid Retriever for Enterprise AI Knowledge Assistant.

Phase 1 Upgrade:
- Pure vector search REPLACED with Hybrid Search
- Combines BM25 (keyword) + Vector (semantic) search
- MMR (Maximal Marginal Relevance) for diversity
- Adaptive top-k based on query complexity
- Re-ranking by combined score

Why Hybrid beats pure vector search:
- Vector search: great for meaning/concept queries
- BM25: great for exact terms, names, numbers, codes
- Hybrid: best of both worlds — 20-30% better retrieval accuracy
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi
from src.embeddings.embedding_model import EmbeddingModel
from src.vectorstore.vector_store import VectorStore
from src.retrieval.reranker import CrossEncoderReranker
from src.utils.logger import setup_logger

logger = setup_logger("HybridRetriever")


class Retriever:
    """
    Hybrid retriever combining BM25 keyword search with
    dense vector semantic search, plus cross-encoder re-ranking
    and MMR diversity filtering.

    Retrieval pipeline:
    Query
      |
      +-- BM25 Search (keyword matching)      --> scores_bm25
      |
      +-- Vector Search (semantic similarity) --> scores_vector
      |
      +-- Score Fusion (RRF algorithm)        --> combined_scores
      |
      +-- Cross-Encoder Re-ranking            --> accurate relevance scores
      |
      +-- MMR Re-ranking (diversity filter)   --> final_chunks
    """

    def __init__(self,
                 embedding_model: EmbeddingModel,
                 vector_store: VectorStore,
                 top_k: int = 5,
                 min_similarity: float = 0.0,
                 bm25_weight: float = 0.3,
                 vector_weight: float = 0.7,
                 mmr_lambda: float = 0.7,
                 use_cross_encoder: bool = True):
        """
        Args:
            embedding_model:   Model for query/document embedding
            vector_store:      ChromaDB vector store
            top_k:              Number of chunks to return
            min_similarity:    Minimum similarity threshold
            bm25_weight:       Weight for BM25 scores (0-1)
            vector_weight:     Weight for vector scores (0-1)
            mmr_lambda:        MMR diversity parameter (0=max diversity, 1=max relevance)
            use_cross_encoder: Re-score fused candidates with a local
                               cross-encoder before MMR, for more accurate
                               relevance ranking than embedding similarity
                               alone. Set False to skip (faster, slightly
                               less accurate — useful for quick local dev).
        """
        self.embedding_model = embedding_model
        self.vector_store    = vector_store
        self.top_k           = top_k
        self.min_similarity  = min_similarity
        self.bm25_weight     = bm25_weight
        self.vector_weight   = vector_weight
        self.mmr_lambda      = mmr_lambda
        self.use_cross_encoder = use_cross_encoder
        self._reranker = CrossEncoderReranker() if use_cross_encoder else None

        # BM25 index (built lazily when first needed)
        self._bm25_index  = None
        self._bm25_corpus = []
        self._bm25_docs   = []

        logger.info(
            f"Hybrid Retriever ready — "
            f"BM25:{bm25_weight} + Vector:{vector_weight}, "
            f"MMR lambda:{mmr_lambda}, top_k:{top_k}, "
            f"cross_encoder:{use_cross_encoder}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(self, query: str,
                 top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Main retrieval method — runs hybrid search + MMR.

        Args:
            query:  User question
            top_k:  Override default top_k

        Returns:
            List of chunk dicts with content, metadata, and scores
        """
        k = top_k or self.top_k

        # Detect query complexity and adapt top_k
        k = self._adaptive_top_k(query, k)

        # Step 1: Vector search
        vector_results = self._vector_search(query, k * 2)

        # Step 2: BM25 search (if index available)
        bm25_results = self._bm25_search(query, k * 2)

        # Step 3: Fuse scores using Reciprocal Rank Fusion
        fused = self._reciprocal_rank_fusion(vector_results, bm25_results)

        # Step 4: Cross-encoder re-ranking — re-scores the fused candidate
        # list with a model that sees (query, chunk) together, which is
        # more accurate than the embedding similarity RRF was based on.
        # Keep a small buffer above k so MMR still has room to trade a
        # little relevance for diversity.
        if self.use_cross_encoder and self._reranker:
            fused = self._reranker.rerank(query, fused, top_n=min(len(fused), k + 3))

        # Step 5: MMR re-ranking for diversity
        final = self._mmr_rerank(query, fused, k)

        # Step 6: Add relevance labels
        final = self._add_relevance_labels(final)

        logger.info(
            f"Hybrid retrieval: {len(vector_results)} vector + "
            f"{len(bm25_results)} BM25 → {len(final)} final chunks"
        )

        return final

    def get_context_text(self, query: str,
                         max_chars: int = 4000) -> str:
        """
        Get formatted context string for LLM prompt.
        Includes source attribution for each chunk.
        """
        chunks = self.retrieve(query)
        if not chunks:
            return ""

        context_parts = []
        total_chars   = 0

        for i, chunk in enumerate(chunks, 1):
            source   = chunk["metadata"].get("source", "Unknown")
            page     = chunk["metadata"].get("page_number", "")
            score    = chunk.get("combined_score", 0)
            label    = chunk.get("relevance_label", "")
            page_str = f", page {page}" if page else ""

            header = (
                f"[Source {i}: {source}{page_str} "
                f"| Relevance: {label}]"
            )
            content = chunk["content"]

            entry      = f"{header}\n{content}"
            entry_size = len(entry)

            if total_chars + entry_size > max_chars:
                # Truncate last chunk to fit
                remaining = max_chars - total_chars
                if remaining > 100:
                    context_parts.append(entry[:remaining] + "...")
                break

            context_parts.append(entry)
            total_chars += entry_size

        return "\n\n---\n\n".join(context_parts)

    def get_sources(self, query: str) -> List[Dict[str, Any]]:
        """Get source chunks for a query (used by /api/chat/sources)."""
        return self.retrieve(query)

    def build_bm25_index(self):
        """
        Build BM25 index from all documents in the vector store.
        Call this after indexing new documents.
        """
        try:
            all_docs = self.vector_store.get_all_documents()
            if not all_docs:
                logger.warning("No documents to build BM25 index from")
                return

            self._bm25_docs   = all_docs
            self._bm25_corpus = [
                self._tokenize(doc["content"]) for doc in all_docs
            ]
            self._bm25_index  = BM25Okapi(self._bm25_corpus)
            logger.info(
                f"BM25 index built with {len(self._bm25_docs)} documents"
            )
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {str(e)}")
            self._bm25_index = None

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _vector_search(self, query: str,
                       k: int) -> List[Dict[str, Any]]:
        """Dense vector semantic search via ChromaDB."""
        try:
            query_embedding = self.embedding_model.embed_text(query)
            results         = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=k
            )
            return results
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []

    def _bm25_search(self, query: str,
                     k: int) -> List[Dict[str, Any]]:
        """BM25 keyword search over indexed documents."""
        if self._bm25_index is None:
            self.build_bm25_index()

        if self._bm25_index is None or not self._bm25_docs:
            return []

        try:
            tokens = self._tokenize(query)
            scores = self._bm25_index.get_scores(tokens)

            # Get top-k indices
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:k]

            results = []
            max_score = max(scores) if max(scores) > 0 else 1.0

            for idx in top_indices:
                if scores[idx] > 0:
                    doc = self._bm25_docs[idx].copy()
                    doc["bm25_score"]  = float(scores[idx])
                    doc["similarity"]  = float(scores[idx] / max_score)
                    results.append(doc)

            return results
        except Exception as e:
            logger.error(f"BM25 search failed: {str(e)}")
            return []

    def _reciprocal_rank_fusion(self,
                                 vector_results: List[Dict],
                                 bm25_results: List[Dict],
                                 k: int = 60) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF) to combine vector and BM25 results.

        RRF score = sum(1 / (k + rank)) for each result list.
        Simple, robust, and consistently outperforms weighted sum approaches.
        """
        scores = {}
        doc_map = {}

        # Score vector results
        for rank, doc in enumerate(vector_results):
            doc_id = self._get_doc_id(doc)
            if doc_id not in scores:
                scores[doc_id]  = 0.0
                doc_map[doc_id] = doc
            scores[doc_id] += self.vector_weight * (1.0 / (k + rank + 1))

        # Score BM25 results
        for rank, doc in enumerate(bm25_results):
            doc_id = self._get_doc_id(doc)
            if doc_id not in scores:
                scores[doc_id]  = 0.0
                doc_map[doc_id] = doc
            scores[doc_id] += self.bm25_weight * (1.0 / (k + rank + 1))

        # Sort by combined score
        sorted_ids = sorted(scores.keys(),
                            key=lambda x: scores[x], reverse=True)

        results = []
        for doc_id in sorted_ids:
            doc = doc_map[doc_id].copy()
            doc["combined_score"] = scores[doc_id]
            results.append(doc)

        return results

    def _mmr_rerank(self, query: str,
                    candidates: List[Dict],
                    k: int) -> List[Dict]:
        """
        Maximal Marginal Relevance (MMR) re-ranking.

        Balances relevance to query vs diversity among selected chunks.
        Prevents returning 5 nearly-identical chunks about the same sentence.

        MMR = argmax [ λ * sim(doc, query) - (1-λ) * max_sim(doc, selected) ]
        """
        if not candidates:
            return []

        if len(candidates) <= k:
            return candidates

        try:
            query_embedding = self.embedding_model.embed_text(query)
            doc_embeddings  = []

            for doc in candidates:
                try:
                    emb = self.embedding_model.embed_text(
                        doc.get("content", "")[:500]
                    )
                    doc_embeddings.append(emb)
                except Exception:
                    doc_embeddings.append([0.0] * 384)

            selected_indices = []
            remaining        = list(range(len(candidates)))

            for _ in range(min(k, len(candidates))):
                if not remaining:
                    break

                best_idx   = None
                best_score = float("-inf")

                for idx in remaining:
                    # Relevance to query
                    relevance = self._cosine_similarity(
                        query_embedding, doc_embeddings[idx]
                    )

                    # Redundancy with already selected
                    if selected_indices:
                        redundancy = max(
                            self._cosine_similarity(
                                doc_embeddings[idx],
                                doc_embeddings[sel_idx]
                            )
                            for sel_idx in selected_indices
                        )
                    else:
                        redundancy = 0.0

                    mmr_score = (
                        self.mmr_lambda * relevance
                        - (1 - self.mmr_lambda) * redundancy
                    )

                    if mmr_score > best_score:
                        best_score = mmr_score
                        best_idx   = idx

                if best_idx is not None:
                    selected_indices.append(best_idx)
                    remaining.remove(best_idx)

            return [candidates[i] for i in selected_indices]

        except Exception as e:
            logger.error(f"MMR reranking failed: {str(e)}")
            return candidates[:k]

    def _adaptive_top_k(self, query: str, base_k: int) -> int:
        """
        Adapt top-k based on query complexity.

        Simple question  → retrieve fewer chunks (less noise)
        Complex question → retrieve more chunks (more context)
        """
        word_count     = len(query.split())
        question_words = ["how", "why", "explain", "compare",
                          "difference", "relationship", "analyze"]
        is_complex     = (
            word_count > 15
            or any(w in query.lower() for w in question_words)
        )

        if is_complex:
            k = min(base_k + 2, 10)
            logger.info(f"Complex query detected → top_k={k}")
        else:
            k = base_k

        return k

    def _add_relevance_labels(self,
                               chunks: List[Dict]) -> List[Dict]:
        """
        Add human-readable relevance labels. Prefers the cross-encoder
        score when available (more accurate — it saw the query and chunk
        together) over the RRF combined_score (based on separately-computed
        embedding/BM25 rankings).
        """
        if not chunks:
            return chunks

        score_key = "cross_encoder_score" if "cross_encoder_score" in chunks[0] else "combined_score"
        max_score = max(c.get(score_key, 0) for c in chunks) or 1.0

        for i, chunk in enumerate(chunks):
            score = chunk.get(score_key, 0)
            ratio = score / max_score

            if ratio >= 0.8:
                label = "High"
            elif ratio >= 0.5:
                label = "Medium"
            else:
                label = "Low"

            chunk["relevance_label"] = label
            chunk["rank"]            = i + 1

        return chunks

    def _cosine_similarity(self, a: List[float],
                            b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b:
            return 0.0
        dot   = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer for BM25 — lowercase, remove punctuation."""
        text   = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        # Remove very short tokens
        return [t for t in tokens if len(t) > 2]

    def _get_doc_id(self, doc: Dict) -> str:
        """Get a unique identifier for a document chunk."""
        source = doc.get("metadata", {}).get("source", "")
        page   = doc.get("metadata", {}).get("page_number", "")
        idx    = doc.get("metadata", {}).get("chunk_index", "")
        content_start = doc.get("content", "")[:50]
        return f"{source}_{page}_{idx}_{content_start}"