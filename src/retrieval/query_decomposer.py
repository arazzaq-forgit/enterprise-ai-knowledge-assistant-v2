"""
Query Decomposer for Enterprise AI Knowledge Assistant.

Phase 4 Upgrade.

Problem this solves:
    A question like "Compare how missing values and duplicate rows are
    handled in pandas" blends TWO distinct retrieval targets into one
    query. A single embedding/BM25 search for that whole sentence tends
    to retrieve chunks that are mediocre matches for BOTH topics, rather
    than great matches for either one individually.

What this does:
    Detects genuinely multi-part questions (cheap heuristic gate — most
    questions are single-intent and skip this entirely, no extra cost)
    and asks the LLM to split them into 2-4 focused sub-questions. Each
    sub-question is retrieved separately, then results are merged and
    de-duplicated before generating the final answer — so retrieval
    quality for each part of the question doesn't get diluted by the
    others.

Cost/latency tradeoff:
    One extra LLM call (decomposition) + one retrieval pass per
    sub-question, but ONLY for questions that look multi-part. Simple
    questions ("What is pandas used for?") skip this entirely and pay
    zero extra cost.
"""

import json
import re
from typing import List
from src.llm.llm_client import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("QueryDecomposer")


class QueryDecomposer:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def _looks_multi_part(self, question: str) -> bool:
        """
        Cheap heuristic gate — only questions that plausibly bundle
        multiple intents get sent to the LLM for real decomposition.
        Deliberately conservative: false negatives (missing a genuinely
        multi-part question) just mean normal single-query retrieval,
        which is safe. False positives just cost one extra LLM call.
        """
        q = question.lower()

        multi_part_signals = [
            " and how ", " and what ", " and why ", " and when ",
            "compare", "difference between", "versus", " vs ",
            "as well as", "also explain", "then explain",
        ]
        has_signal = any(sig in q for sig in multi_part_signals)

        # Multiple question marks = literally multiple questions
        has_multiple_questions = question.count("?") > 1

        # Long questions with a conjunction are more likely compound
        is_long_with_and = len(question.split()) > 12 and " and " in q

        return has_signal or has_multiple_questions or is_long_with_and

    def decompose(self, question: str, max_sub_questions: int = 4) -> List[str]:
        """
        Returns a list of sub-questions. Returns [question] unchanged
        (a list of one) if the question doesn't look multi-part, or if
        decomposition fails for any reason — callers can always safely
        iterate the result without checking whether decomposition
        actually happened.
        """
        if not self._looks_multi_part(question):
            return [question]

        prompt = f"""Break the following question into 2-4 focused, standalone sub-questions if it genuinely covers multiple distinct topics. If it's really just one topic, return it unchanged as a single-item list.

Question: {question}

Respond with ONLY a JSON array of strings, nothing else. Example: ["sub-question one", "sub-question two"]"""

        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You decompose questions into sub-questions. Respond with ONLY a JSON array of strings, no other text."
            )

            # Models sometimes wrap JSON in markdown code fences despite
            # instructions — strip those before parsing.
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.strip())
            sub_questions = json.loads(cleaned)

            if not isinstance(sub_questions, list) or not all(isinstance(s, str) for s in sub_questions):
                raise ValueError("Response wasn't a list of strings")

            sub_questions = [s.strip() for s in sub_questions if s.strip()][:max_sub_questions]

            if not sub_questions:
                return [question]

            if len(sub_questions) > 1:
                logger.info(f"Decomposed into {len(sub_questions)} sub-questions: {sub_questions}")

            return sub_questions

        except Exception as e:
            logger.warning(f"Decomposition failed ({e}), using original question unchanged")
            return [question]