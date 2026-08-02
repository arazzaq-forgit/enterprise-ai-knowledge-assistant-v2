"""
RAGAS-lite: lightweight retrieval/answer quality metrics for DocMind AI.

Phase 3 Upgrade.

Real RAGAS (https://github.com/explodinggecko/ragas) uses an LLM-as-judge
to decompose answers into claims and verify each one — accurate, but slow
and expensive (many extra LLM calls per question). This module implements
the same four core metrics using embeddings you already have (the HF
Inference API embedding model) plus the existing hallucination detector,
so evaluation runs fast and free, and results are directly comparable
run-to-run without LLM non-determinism.

Metrics:
    context_precision — of the chunks retrieved, what fraction are
                         actually relevant to the question?
                         (signal-to-noise of the retriever)
    context_recall     — does the retrieved context semantically cover a
                         reference/ground-truth answer, if one is given?
                         (did retrieval miss something important?)
    answer_relevance   — does the answer actually address the question?
                         (semantic similarity, question vs answer)
    faithfulness       — is the answer grounded in the retrieved context,
                         or does it drift into unsupported claims?
                         (reuses HallucinationDetector, inverted to a
                         0-1 "faithfulness" score)

All scores are 0.0 (worst) to 1.0 (best). context_recall is None when no
reference answer is supplied for a question (it's optional per-sample).
"""

from typing import List, Dict, Any, Optional
import numpy as np

from src.embeddings.embedding_model import EmbeddingModel
from src.evaluation.hallucination_detector import HallucinationDetector
from src.utils.logger import setup_logger

logger = setup_logger("RagasLite")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    va, vb = np.array(a, dtype=float), np.array(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


class RagasLiteMetrics:
    def __init__(self,
                 embedding_model: EmbeddingModel,
                 relevance_threshold: float = 0.35):
        """
        Args:
            embedding_model:     shared EmbeddingModel instance (reuse the
                                  pipeline's, don't create a second one)
            relevance_threshold: cosine similarity above which a retrieved
                                  chunk counts as "relevant" for
                                  context_precision. 0.35 is a reasonable
                                  default for all-MiniLM-L6-v2; tune it
                                  against a few hand-labeled examples if
                                  you want a stricter/looser bar.
        """
        self.embed = embedding_model
        self.hallucination_detector = HallucinationDetector()
        self.relevance_threshold = relevance_threshold

    def context_precision(self, question: str, chunks: List[Dict[str, Any]]) -> Optional[float]:
        """
        Fraction of retrieved chunks that are semantically relevant to the
        question. Returns None (not 0.0) if the embedding API is
        unreachable — None means "couldn't measure", 0.0 would falsely
        imply "measured and found zero relevant chunks".
        """
        if not chunks:
            return 0.0
        try:
            q_vec = self.embed.embed_text(question)
            relevant = 0
            for c in chunks:
                content = (c.get("content") or "")[:1000]
                if not content.strip():
                    continue
                c_vec = self.embed.embed_text(content)
                if cosine_similarity(q_vec, c_vec) >= self.relevance_threshold:
                    relevant += 1
            return round(relevant / len(chunks), 3)
        except Exception as e:
            logger.warning(f"context_precision skipped (embedding API unavailable): {e}")
            return None

    def context_recall(self,
                        reference_answer: Optional[str],
                        chunks: List[Dict[str, Any]]) -> Optional[float]:
        """
        Does the retrieved context semantically cover the reference answer?
        Returns None if no reference answer was supplied, OR if the
        embedding API is unreachable.
        """
        if not reference_answer or not chunks:
            return None
        try:
            ref_vec = self.embed.embed_text(reference_answer)
            context_text = " ".join((c.get("content") or "") for c in chunks)[:4000]
            if not context_text.strip():
                return 0.0
            ctx_vec = self.embed.embed_text(context_text)
            return round(cosine_similarity(ref_vec, ctx_vec), 3)
        except Exception as e:
            logger.warning(f"context_recall skipped (embedding API unavailable): {e}")
            return None

    def answer_relevance(self, question: str, answer: str) -> Optional[float]:
        """How well the answer semantically addresses the question."""
        if not answer or not answer.strip():
            return 0.0
        try:
            q_vec = self.embed.embed_text(question)
            a_vec = self.embed.embed_text(answer)
            return round(cosine_similarity(q_vec, a_vec), 3)
        except Exception as e:
            logger.warning(f"answer_relevance skipped (embedding API unavailable): {e}")
            return None

    def faithfulness(self, answer: str, chunks: List[Dict[str, Any]], question: str = "") -> Optional[float]:
        """How grounded the answer is in the retrieved context (1 - hallucination risk)."""
        if not answer or not chunks:
            return 0.0
        try:
            result = self.hallucination_detector.detect(
                answer=answer, retrieved_chunks=chunks, question=question
            )
            risk_score = result.get("risk_score", 100)
            return round(max(0.0, 1 - (risk_score / 100)), 3)
        except Exception as e:
            logger.warning(f"faithfulness skipped (hallucination detector failed): {e}")
            return None

    def evaluate_sample(self,
                         question: str,
                         answer: str,
                         chunks: List[Dict[str, Any]],
                         reference_answer: Optional[str] = None) -> Dict[str, Any]:
        """
        Compute all four metrics for one (question, answer, context) sample.
        Each metric fails independently — one flaky embedding API call
        skips that metric (returns None) rather than crashing the whole
        batch evaluation run.
        """
        return {
            "context_precision": self.context_precision(question, chunks),
            "context_recall":    self.context_recall(reference_answer, chunks),
            "answer_relevance":  self.answer_relevance(question, answer),
            "faithfulness":      self.faithfulness(answer, chunks, question),
        }