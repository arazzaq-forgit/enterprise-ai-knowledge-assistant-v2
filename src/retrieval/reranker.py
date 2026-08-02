"""
Cross-Encoder Re-ranker for Enterprise AI Knowledge Assistant.

Phase 4 Upgrade.

Why this runs LOCALLY instead of via the HuggingFace Inference API
(unlike embeddings, which do use the API):
    HuggingFace's Inference API does not currently serve
    cross-encoder/ms-marco-MiniLM-L-6-v2 ("This model isn't deployed by
    any Inference Provider" per its model page) — so an HTTP call would
    just fail. sentence-transformers (already a project dependency)
    downloads the model once (~90MB) and runs it locally via PyTorch.
    It's small and fast enough on CPU for reranking a handful of
    candidate chunks per query.

What a cross-encoder does differently from the embedding model:
    The embedding model encodes the query and each chunk SEPARATELY,
    then compares vectors — fast, but the model never sees the query
    and chunk together, so it misses interaction between them.

    A cross-encoder feeds the (query, chunk) pair into the model
    TOGETHER and outputs a single relevance score. Much more accurate
    per-pair judgment, but slower — which is why it's used to re-rank a
    small shortlist (10-20 candidates) rather than search the whole
    document collection.
"""

from typing import List, Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger("CrossEncoderReranker")


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Lazy-loads the model on first use (not in __init__) so that
        importing/constructing a Retriever doesn't force a ~90MB model
        download + torch import if re-ranking ends up disabled or unused.
        """
        self.model_name = model_name
        self._model = None
        self._load_failed = False

    def _ensure_loaded(self) -> bool:
        if self._model is not None:
            return True
        if self._load_failed:
            return False
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading cross-encoder '{self.model_name}' (first use only)...")
            self._model = CrossEncoder(self.model_name)
            logger.info("Cross-encoder ready")
            return True
        except Exception as e:
            logger.error(f"Failed to load cross-encoder, re-ranking disabled: {e}")
            self._load_failed = True
            return False

    def rerank(self,
               query: str,
               candidates: List[Dict[str, Any]],
               top_n: int) -> List[Dict[str, Any]]:
        """
        Score each (query, chunk) pair with the cross-encoder and return
        the top_n candidates sorted by that score, each tagged with
        'cross_encoder_score'.

        Falls back to returning the first top_n candidates UNCHANGED
        (preserving whatever order they arrived in) if the model can't
        be loaded — re-ranking is a quality improvement, not a hard
        dependency, so a missing/corrupted local model download should
        degrade gracefully rather than break retrieval entirely.
        """
        if not candidates:
            return []

        if not self._ensure_loaded():
            return candidates[:top_n]

        try:
            pairs = [(query, c.get("content", "")[:1000]) for c in candidates]
            scores = self._model.predict(pairs)

            for c, score in zip(candidates, scores):
                c["cross_encoder_score"] = float(score)

            reranked = sorted(candidates, key=lambda c: c["cross_encoder_score"], reverse=True)
            return reranked[:top_n]

        except Exception as e:
            logger.error(f"Cross-encoder scoring failed, returning unranked candidates: {e}")
            return candidates[:top_n]