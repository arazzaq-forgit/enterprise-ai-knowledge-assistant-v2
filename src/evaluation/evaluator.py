"""
Evaluator for Enterprise AI Knowledge Assistant.
Measures and scores the quality of RAG responses.
"""

import re
import time
from typing import List, Dict, Any, Optional
from src.utils.logger import setup_logger
from src.utils.helpers import TextHelper, TimeHelper

logger = setup_logger("Evaluator")


class RAGEvaluator:
    """
    Evaluates quality of RAG pipeline responses.

    Why evaluation matters for internship?
        Any production AI system needs metrics.
        This shows you think beyond just building —
        you also measure, monitor and improve!

    Metrics tracked:
        ✅ Relevance Score   — how relevant is answer
        ✅ Coverage Score    — how complete is answer
        ✅ Source Score      — are sources cited
        ✅ Response Time     — how fast is answer
        ✅ Faithfulness      — stays true to context
        ✅ Overall Score     — combined quality grade
    """

    def __init__(self):
        self.evaluation_history: List[Dict] = []
        logger.info("RAG Evaluator initialized")

    # ════════════════════════════════════════════════════════════
    #  CORE METRICS
    # ════════════════════════════════════════════════════════════

    def score_relevance(self,
                        question: str,
                        answer: str) -> float:
        """
        Score how relevant the answer is to question.
        Uses keyword overlap as a simple metric.

        Returns:
            Score between 0.0 and 1.0
        """
        if not answer or not question:
            return 0.0

        # Extract keywords from question and answer
        q_keywords = set(
            TextHelper.extract_keywords(question, top_n=10)
        )
        a_keywords = set(
            TextHelper.extract_keywords(answer, top_n=20)
        )

        if not q_keywords:
            return 0.5

        # Calculate overlap
        overlap = q_keywords.intersection(a_keywords)
        score   = len(overlap) / len(q_keywords)

        return round(min(score, 1.0), 3)

    def score_coverage(self,
                       answer: str,
                       context: str) -> float:
        """
        Score how well answer covers the context.
        Higher = answer uses more of available info.

        Returns:
            Score between 0.0 and 1.0
        """
        if not answer or not context:
            return 0.0

        # Extract keywords from both
        a_keywords = set(
            TextHelper.extract_keywords(answer, top_n=20)
        )
        c_keywords = set(
            TextHelper.extract_keywords(context, top_n=30)
        )

        if not c_keywords:
            return 0.5

        overlap = a_keywords.intersection(c_keywords)
        score   = len(overlap) / len(c_keywords)

        return round(min(score * 2, 1.0), 3)

    def score_sources(self,
                      answer: str,
                      sources: List[Dict]) -> float:
        """
        Score whether answer properly cites sources.

        Returns:
            Score between 0.0 and 1.0
        """
        if not sources:
            return 0.0

        score = 0.0

        # Check if answer mentions source names
        source_names = [
            s.get("metadata", {}).get("source", "")
            for s in sources
        ]

        mentions = sum(
            1 for name in source_names
            if name and name.lower() in answer.lower()
        )

        if mentions > 0:
            score += 0.5

        # Check if answer has structured response
        has_structure = any([
            "•"  in answer,
            "-"  in answer,
            "1." in answer,
            "\n" in answer,
        ])

        if has_structure:
            score += 0.3

        # Check answer length is reasonable
        word_count = TextHelper.count_words(answer)
        if 50 <= word_count <= 500:
            score += 0.2

        return round(min(score, 1.0), 3)

    def score_faithfulness(self,
                           answer: str,
                           context: str) -> float:
        """
        Score if answer stays faithful to context.
        Checks for hallucination indicators.

        Returns:
            Score between 0.0 and 1.0
        """
        if not answer or not context:
            return 0.0

        score = 1.0

        # Penalise if answer says "I don't know"
        # but context has relevant info
        uncertainty_phrases = [
            "i don't know",
            "i cannot find",
            "not mentioned",
            "no information",
        ]

        has_uncertainty = any(
            phrase in answer.lower()
            for phrase in uncertainty_phrases
        )

        context_has_info = (
            TextHelper.count_words(context) > 50
        )

        if has_uncertainty and context_has_info:
            score -= 0.3

        # Check answer doesn't have hallucination signals
        hallucination_phrases = [
            "as an ai",
            "i believe",
            "i think",
            "probably",
            "i assume",
        ]

        hallucinations = sum(
            1 for phrase in hallucination_phrases
            if phrase in answer.lower()
        )

        score -= hallucinations * 0.1

        return round(max(score, 0.0), 3)

    def score_response_time(self,
                            response_time: float) -> float:
        """
        Score based on response time.
        Faster = better score.

        Returns:
            Score between 0.0 and 1.0
        """
        if response_time <= 2:
            return 1.0
        elif response_time <= 5:
            return 0.8
        elif response_time <= 10:
            return 0.6
        elif response_time <= 20:
            return 0.4
        elif response_time <= 30:
            return 0.2
        else:
            return 0.1

    # ════════════════════════════════════════════════════════════
    #  OVERALL EVALUATION
    # ════════════════════════════════════════════════════════════

    def evaluate_response(self,
                          question: str,
                          answer: str,
                          context: str,
                          sources: List[Dict],
                          response_time: float
                          ) -> Dict[str, Any]:
        """
        Run complete evaluation on a RAG response.

        Args:
            question:      User question
            answer:        AI generated answer
            context:       Retrieved context used
            sources:       Source documents
            response_time: Time taken in seconds

        Returns:
            Complete evaluation report
        """
        logger.info(f"Evaluating response for: "
                    f"'{question[:40]}...'")

        # ── Calculate all scores ─────────────────────────────────
        relevance    = self.score_relevance(question, answer)
        coverage     = self.score_coverage(answer, context)
        sources_score = self.score_sources(answer, sources)
        faithfulness = self.score_faithfulness(
                           answer, context
                       )
        speed        = self.score_response_time(
                           response_time
                       )

        # ── Calculate weighted overall score ─────────────────────
        overall = round(
            relevance    * 0.30 +
            coverage     * 0.20 +
            sources_score * 0.20 +
            faithfulness * 0.20 +
            speed        * 0.10,
            3
        )

        # ── Get grade ────────────────────────────────────────────
        grade = self._get_grade(overall)

        evaluation = {
            "timestamp":     TimeHelper.get_timestamp(),
            "question":      question[:100],
            "scores": {
                "relevance":    relevance,
                "coverage":     coverage,
                "sources":      sources_score,
                "faithfulness": faithfulness,
                "speed":        speed,
                "overall":      overall,
            },
            "grade":          grade,
            "response_time":  response_time,
            "word_count":     TextHelper.count_words(answer),
            "sources_used":   len(sources),
        }

        # ── Save to history ──────────────────────────────────────
        self.evaluation_history.append(evaluation)

        logger.info(
            f"Evaluation complete: "
            f"overall={overall}, grade={grade}"
        )
        return evaluation

    def _get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return "A+ 🌟"
        elif score >= 0.8:
            return "A  ✅"
        elif score >= 0.7:
            return "B+ 👍"
        elif score >= 0.6:
            return "B  📊"
        elif score >= 0.5:
            return "C  ⚠️"
        else:
            return "D  ❌"

    # ════════════════════════════════════════════════════════════
    #  ANALYTICS
    # ════════════════════════════════════════════════════════════

    def get_average_scores(self) -> Dict[str, float]:
        """Get average scores across all evaluations."""
        if not self.evaluation_history:
            return {}

        metrics = [
            "relevance", "coverage",
            "sources", "faithfulness",
            "speed", "overall"
        ]
        averages = {}

        for metric in metrics:
            scores = [
                e["scores"].get(metric, 0)
                for e in self.evaluation_history
            ]
            averages[metric] = round(
                sum(scores) / len(scores), 3
            )

        return averages

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all evaluations.
        Displayed in UI analytics dashboard.
        """
        if not self.evaluation_history:
            return {
                "total_evaluations": 0,
                "message": "No evaluations yet"
            }

        avg_scores = self.get_average_scores()
        grades = [
            e["grade"]
            for e in self.evaluation_history
        ]

        return {
            "total_evaluations": len(
                self.evaluation_history
            ),
            "average_scores":    avg_scores,
            "best_grade":        min(grades),
            "average_overall":   avg_scores.get(
                                     "overall", 0
                                 ),
            "avg_response_time": round(
                sum(
                    e["response_time"]
                    for e in self.evaluation_history
                ) / len(self.evaluation_history),
                2
            ),
        }

    def get_improvement_tips(self,
                             scores: Dict[str, float]
                             ) -> List[str]:
        """
        Give actionable tips based on scores.
        Shown to user in UI.
        """
        tips = []

        if scores.get("relevance", 1) < 0.5:
            tips.append(
                "💡 Try rephrasing your question "
                "with more specific keywords"
            )

        if scores.get("coverage", 1) < 0.5:
            tips.append(
                "📄 Upload more related documents "
                "to improve coverage"
            )

        if scores.get("sources", 1) < 0.5:
            tips.append(
                "📚 The answer may need better "
                "source documents"
            )

        if scores.get("speed", 1) < 0.5:
            tips.append(
                "⚡ Response is slow — consider "
                "using a smaller model"
            )

        if not tips:
            tips.append(
                "✅ Great response quality! "
                "Keep asking questions!"
            )

        return tips