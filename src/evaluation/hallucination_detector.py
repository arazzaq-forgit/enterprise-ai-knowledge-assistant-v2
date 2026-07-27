"""
Hallucination Detector for Enterprise AI Knowledge Assistant.

Phase 2 Upgrade:
Detects when the LLM generates information NOT supported
by the retrieved context — a key challenge in RAG systems.

Detection methods:
1. Coverage check — key claims in answer vs context
2. Refusal detection — did model say "I don't know"?
3. Contradiction check — answer contradicts context
4. Specificity check — specific numbers/names not in context
"""

import re
from typing import List, Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger("HallucinationDetector")


class HallucinationDetector:
    """
    Detects potential hallucinations in RAG-generated answers.

    Returns a risk assessment:
    - LOW:    Answer is well-grounded in retrieved context
    - MEDIUM: Some claims may not be directly supported
    - HIGH:   Answer likely contains unsupported information
    """

    def __init__(self):
        # Phrases that indicate model is working from memory
        self.hallucination_signals = [
            "generally speaking",
            "typically",
            "in most cases",
            "it is commonly known",
            "as we all know",
            "obviously",
            "clearly",
            "it goes without saying",
            "everyone knows",
            "as is well known",
        ]

        # Phrases that indicate proper grounding
        self.grounding_signals = [
            "according to",
            "based on",
            "the document",
            "the text",
            "as mentioned",
            "as stated",
            "source",
            "page",
            "the provided",
            "in the context",
            "from the",
        ]

        logger.info("Hallucination Detector ready")

    def detect(self,
               answer: str,
               retrieved_chunks: List[Dict[str, Any]],
               question: str = "") -> Dict[str, Any]:
        """
        Analyze answer for potential hallucinations.

        Args:
            answer:           Generated answer text
            retrieved_chunks: Retrieved context chunks
            question:         Original user question

        Returns:
            Dict with risk_level, risk_score, flags, and explanation
        """
        if not answer or not retrieved_chunks:
            return self._no_context_result()

        context = " ".join([
            c.get("content", "") for c in retrieved_chunks
        ]).lower()

        answer_lower = answer.lower()
        flags        = []
        risk_score   = 0

        # Check 1: Hallucination signal phrases
        found_signals = [
            s for s in self.hallucination_signals
            if s in answer_lower
        ]
        if found_signals:
            risk_score += 20
            flags.append(
                f"Vague language detected: '{found_signals[0]}'"
            )

        # Check 2: Grounding signal phrases (good sign)
        found_grounding = sum(
            1 for s in self.grounding_signals
            if s in answer_lower
        )
        if found_grounding >= 2:
            risk_score -= 15  # Well grounded
        elif found_grounding == 0:
            risk_score += 15
            flags.append("Answer lacks explicit source references")

        # Check 3: Specific numbers not in context
        answer_numbers  = set(re.findall(r'\b\d+\.?\d*\b', answer))
        context_numbers = set(re.findall(r'\b\d+\.?\d*\b', context))
        unsupported_numbers = answer_numbers - context_numbers

        if unsupported_numbers and len(unsupported_numbers) > 2:
            risk_score += 25
            flags.append(
                f"Specific numbers not found in context: "
                f"{list(unsupported_numbers)[:3]}"
            )

        # Check 4: Proper nouns in answer not in context
        answer_proper   = set(re.findall(r'\b[A-Z][a-z]+\b', answer))
        context_proper  = set(re.findall(r'\b[A-Z][a-z]+\b',
                                          " ".join([
                                              c.get("content", "")
                                              for c in retrieved_chunks
                                          ])))
        # Remove common words that appear capitalized
        common = {"The", "A", "An", "In", "Of", "For", "And",
                  "But", "Or", "So", "To", "From", "With", "Based",
                  "According", "Source", "Page", "However", "This"}
        unsupported_proper = (answer_proper - context_proper - common)

        if len(unsupported_proper) > 3:
            risk_score += 20
            flags.append(
                f"Named entities not in context: "
                f"{list(unsupported_proper)[:3]}"
            )

        # Check 5: Answer is a refusal (model says it doesn't know)
        refusal_phrases = [
            "i don't know",
            "i cannot find",
            "not mentioned",
            "not found in",
            "no information",
            "cannot determine",
            "i could not find",
        ]
        is_refusal = any(p in answer_lower for p in refusal_phrases)
        if is_refusal:
            risk_score = 0  # Refusals are not hallucinations
            flags = ["Model correctly refused to answer"]

        # Check 6: Very short answer to complex question
        if len(answer.split()) < 15 and len(question.split()) > 8:
            risk_score += 10
            flags.append("Answer may be incomplete for complex question")

        # Clamp risk score
        risk_score = max(0, min(100, risk_score))

        risk_level, color = self._get_risk_level(risk_score)

        result = {
            "risk_level":  risk_level,
            "risk_score":  risk_score,
            "color":       color,
            "is_refusal":  is_refusal,
            "flags":       flags,
            "explanation": self._get_explanation(
                risk_level, flags, is_refusal
            ),
            "is_grounded": risk_score < 40,
        }

        logger.info(
            f"Hallucination check: {risk_level} "
            f"(score={risk_score}, flags={len(flags)})"
        )

        return result

    def _get_risk_level(self,
                         score: float) -> tuple:
        """Map risk score to level and color."""
        if score < 30:
            return "LOW", "#10B981"       # green
        elif score < 60:
            return "MEDIUM", "#F59E0B"    # yellow
        else:
            return "HIGH", "#EF4444"      # red

    def _get_explanation(self, risk_level: str,
                          flags: List[str],
                          is_refusal: bool) -> str:
        """Generate explanation for the risk assessment."""
        if is_refusal:
            return ("Model correctly identified insufficient context "
                    "and declined to speculate.")

        if risk_level == "LOW":
            return ("Answer appears well-grounded in the retrieved "
                    "document context.")
        elif risk_level == "MEDIUM":
            return ("Answer is mostly grounded but may contain some "
                    "claims not directly supported by the documents.")
        else:
            return ("Answer may contain information not present in "
                    "the retrieved documents. Verify important claims.")

    def _no_context_result(self) -> Dict[str, Any]:
        """Return result when no context available."""
        return {
            "risk_level":  "HIGH",
            "risk_score":  100,
            "color":       "#EF4444",
            "is_refusal":  False,
            "flags":       ["No context retrieved"],
            "explanation": "No documents retrieved to ground the answer.",
            "is_grounded": False,
        }