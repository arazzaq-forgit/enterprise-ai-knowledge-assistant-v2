"""
Confidence Scorer for Enterprise AI Knowledge Assistant.

Phase 2 Upgrade:
Calculates confidence score for each RAG answer based on:
- Retrieval quality (similarity scores of retrieved chunks)
- Context coverage (how much of the answer is grounded)
- Source diversity (number of different sources used)
- Query-context alignment (semantic similarity)
"""

import re
from typing import List, Dict, Any, Tuple
from src.utils.logger import setup_logger

logger = setup_logger("ConfidenceScorer")


class ConfidenceScorer:
    """
    Scores RAG answers on a 0-100 confidence scale.

    Scoring components:
    - Retrieval score (40%): Average similarity of retrieved chunks
    - Coverage score (30%): Fraction of answer terms found in context
    - Source score  (20%): Number and diversity of sources cited
    - Length score  (10%): Answer completeness vs context richness

    Final score maps to:
    - 75-100: High confidence   (green badge)
    - 50-74:  Medium confidence (yellow badge)
    - 0-49:   Low confidence    (red badge)
    """

    def __init__(self):
        logger.info("Confidence Scorer ready")

    def score(self,
              question: str,
              answer: str,
              retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate confidence score for a RAG answer.

        Args:
            question:         User's question
            answer:           Generated answer
            retrieved_chunks: List of retrieved chunk dicts with similarity scores

        Returns:
            Dict with score, label, components, and explanation
        """
        if not retrieved_chunks:
            return self._no_context_score()

        # Component 1: Retrieval quality score (0-100)
        retrieval_score = self._retrieval_quality_score(retrieved_chunks)

        # Component 2: Coverage score (0-100)
        coverage_score = self._coverage_score(answer, retrieved_chunks)

        # Component 3: Source diversity score (0-100)
        source_score = self._source_diversity_score(retrieved_chunks)

        # Component 4: Answer completeness score (0-100)
        completeness_score = self._completeness_score(answer, question)

        # Weighted final score
        final_score = (
            retrieval_score    * 0.40 +
            coverage_score     * 0.30 +
            source_score       * 0.20 +
            completeness_score * 0.10
        )

        final_score = round(min(100, max(0, final_score)))

        label, color = self._get_label(final_score)

        result = {
            "score":       final_score,
            "label":       label,
            "color":       color,
            "percentage":  f"{final_score}%",
            "components": {
                "retrieval":    round(retrieval_score),
                "coverage":     round(coverage_score),
                "sources":      round(source_score),
                "completeness": round(completeness_score),
            },
            "explanation": self._get_explanation(
                final_score, retrieval_score,
                coverage_score, source_score
            ),
        }

        logger.info(
            f"Confidence: {final_score}% ({label}) — "
            f"retrieval={round(retrieval_score)}, "
            f"coverage={round(coverage_score)}, "
            f"sources={round(source_score)}"
        )

        return result

    def _retrieval_quality_score(self,
                                  chunks: List[Dict]) -> float:
        """Score based on similarity scores of retrieved chunks."""
        similarities = []
        for chunk in chunks:
            sim = chunk.get("similarity", 0)
            if sim:
                similarities.append(float(sim))

        if not similarities:
            return 50.0

        avg_sim = sum(similarities) / len(similarities)
        max_sim = max(similarities)

        # Weight average and max similarity
        score = (avg_sim * 0.6 + max_sim * 0.4) * 100
        return min(100, score)

    def _coverage_score(self, answer: str,
                         chunks: List[Dict]) -> float:
        """
        Score based on how many answer terms appear in retrieved context.
        High coverage = answer is grounded in retrieved text.
        Low coverage = possible hallucination.
        """
        if not answer or not chunks:
            return 0.0

        # Get all context text
        context = " ".join([
            c.get("content", "") for c in chunks
        ]).lower()

        # Extract meaningful words from answer (exclude stopwords)
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may",
            "might", "shall", "can", "need", "dare", "ought",
            "used", "to", "of", "in", "for", "on", "with", "at",
            "by", "from", "up", "about", "into", "through", "during",
            "and", "but", "or", "nor", "not", "so", "yet", "both",
            "either", "neither", "this", "that", "these", "those",
            "i", "me", "my", "we", "our", "you", "your", "it",
            "its", "they", "them", "their", "what", "which", "who",
        }

        answer_words = set(
            w.lower() for w in re.findall(r'\b\w+\b', answer)
            if len(w) > 3 and w.lower() not in stopwords
        )

        if not answer_words:
            return 60.0

        # Count how many answer words appear in context
        found = sum(1 for w in answer_words if w in context)
        coverage = found / len(answer_words)

        return min(100, coverage * 100)

    def _source_diversity_score(self,
                                 chunks: List[Dict]) -> float:
        """Score based on number and diversity of sources."""
        if not chunks:
            return 0.0

        sources = set()
        for chunk in chunks:
            source = chunk.get("metadata", {}).get("source", "")
            if source:
                sources.add(source)

        num_chunks   = len(chunks)
        num_sources  = len(sources)

        # More chunks = more context = higher confidence
        chunk_score  = min(100, num_chunks * 20)

        # Multiple sources = more diverse context
        source_score = min(100, num_sources * 40)

        return (chunk_score * 0.6 + source_score * 0.4)

    def _completeness_score(self, answer: str,
                              question: str) -> float:
        """Score based on answer length and completeness."""
        if not answer:
            return 0.0

        word_count = len(answer.split())

        # Very short answers are likely incomplete
        if word_count < 10:
            return 20.0
        elif word_count < 30:
            return 50.0
        elif word_count < 100:
            return 75.0
        else:
            return 90.0

    def _get_label(self, score: float) -> Tuple[str, str]:
        """Map score to human-readable label and color."""
        if score >= 75:
            return "High", "#10B981"      # green
        elif score >= 50:
            return "Medium", "#F59E0B"    # yellow
        else:
            return "Low", "#EF4444"       # red

    def _get_explanation(self, score: float,
                          retrieval: float,
                          coverage: float,
                          sources: float) -> str:
        """Generate human-readable explanation of the score."""
        parts = []

        if retrieval >= 70:
            parts.append("highly relevant chunks retrieved")
        elif retrieval >= 40:
            parts.append("moderately relevant chunks retrieved")
        else:
            parts.append("low relevance chunks retrieved")

        if coverage >= 70:
            parts.append("answer well-grounded in documents")
        elif coverage >= 40:
            parts.append("answer partially grounded in documents")
        else:
            parts.append("answer may contain unsupported claims")

        if sources >= 60:
            parts.append("multiple sources consulted")

        return "; ".join(parts).capitalize() + "."

    def _no_context_score(self) -> Dict[str, Any]:
        """Return zero confidence when no context retrieved."""
        return {
            "score":      0,
            "label":      "No Context",
            "color":      "#6B7280",
            "percentage": "0%",
            "components": {
                "retrieval":    0,
                "coverage":     0,
                "sources":      0,
                "completeness": 0,
            },
            "explanation": "No documents retrieved for this question.",
        }