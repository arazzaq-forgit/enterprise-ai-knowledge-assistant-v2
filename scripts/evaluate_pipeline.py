"""
Phase 3 — Evaluation Framework CLI.

Batch-runs a set of test questions through:
  (a) the full RAG pipeline (retrieval + generation)
  (b) a no-RAG baseline (LLM answering from its own knowledge only,
      no retrieved context at all)

...and scores every answer with RAGAS-lite metrics (context precision,
context recall, answer relevance, faithfulness). Produces:
  - a console summary table (averages, RAG vs no-RAG)
  - data/eval/results_<timestamp>.csv   (per-question rows, for Excel/plots)
  - data/eval/results_<timestamp>.json  (full detail incl. answers/sources)

USAGE
-----
    # 1. Make sure you've already uploaded the documents your test
    #    questions are about, via the running app (this script reuses
    #    whatever is currently in data/vectorstore).
    #
    # 2. Run against the bundled sample test set:
    python scripts/evaluate_pipeline.py

    # 3. Or your own test set:
    python scripts/evaluate_pipeline.py --testset data/eval/my_questions.json

    # 4. Skip the no-RAG baseline (faster, RAG-only scoring):
    python scripts/evaluate_pipeline.py --no-baseline

TEST SET FORMAT (data/eval/sample_testset.json)
------------------------------------------------
    [
      {
        "question": "What is the refund policy?",
        "reference_answer": "Refunds are issued within 30 days of purchase."
      },
      {
        "question": "Who is the CEO?"
        // reference_answer is optional — if omitted, context_recall
        // is skipped for that question (still get everything else)
      }
    ]
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

# Allow running as `python scripts/evaluate_pipeline.py` from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.rag_pipeline import RAGPipeline
from src.evaluation.ragas_metrics import RagasLiteMetrics
from src.prompts.prompt_template import PromptTemplates


def load_testset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError(f"Test set at {path} must be a non-empty JSON list.")
    for i, item in enumerate(data):
        if "question" not in item:
            raise ValueError(f"Test set item {i} is missing required 'question' field.")
    return data


def run_no_rag_baseline(pipeline: RAGPipeline, question: str) -> str:
    """Answer using only the LLM's own knowledge — no retrieval, no document context."""
    baseline_prompt = (
        f"Answer the following question directly and concisely, using only "
        f"your own general knowledge (do not assume access to any documents):\n\n"
        f"Question: {question}"
    )
    return pipeline.llm.generate(
        prompt=baseline_prompt,
        system_prompt="You are a helpful assistant answering from general knowledge."
    )


def evaluate(testset_path: str, include_baseline: bool = True) -> Dict[str, Any]:
    print(f"Loading pipeline...")
    pipeline = RAGPipeline()

    if pipeline.vector_store.count() == 0:
        print(
            "\n⚠️  WARNING: No documents are indexed in the vector store.\n"
            "   Upload documents via the running app first, or RAG results\n"
            "   will be meaningless (empty context for every question).\n"
        )

    metrics = RagasLiteMetrics(embedding_model=pipeline.embedding_model)
    testset = load_testset(testset_path)
    print(f"Loaded {len(testset)} test questions from {testset_path}\n")

    rows: List[Dict[str, Any]] = []

    for i, item in enumerate(testset, 1):
        question = item["question"]
        reference_answer = item.get("reference_answer")
        print(f"[{i}/{len(testset)}] {question[:70]}")

        # ---- RAG path ----
        t0 = time.time()
        rag_result = pipeline.ask_with_evaluation(question=question)
        rag_time = round(time.time() - t0, 2)
        chunks = pipeline.retriever.retrieve(question)  # full-content chunks for scoring

        rag_scores = metrics.evaluate_sample(
            question=question,
            answer=rag_result["answer"],
            chunks=chunks,
            reference_answer=reference_answer,
        )

        row = {
            "question": question,
            "reference_answer": reference_answer or "",
            "rag_answer": rag_result["answer"],
            "rag_response_time_s": rag_time,
            "rag_context_precision": rag_scores["context_precision"],
            "rag_context_recall": rag_scores["context_recall"],
            "rag_answer_relevance": rag_scores["answer_relevance"],
            "rag_faithfulness": rag_scores["faithfulness"],
            "rag_confidence_score": rag_result["confidence"].get("score"),
            "rag_hallucination_risk": rag_result["hallucination_check"].get("risk_level"),
            "num_chunks_retrieved": len(chunks),
        }

        # ---- No-RAG baseline ----
        if include_baseline:
            t0 = time.time()
            baseline_answer = run_no_rag_baseline(pipeline, question)
            baseline_time = round(time.time() - t0, 2)
            baseline_relevance = metrics.answer_relevance(question, baseline_answer)

            row.update({
                "baseline_answer": baseline_answer,
                "baseline_response_time_s": baseline_time,
                "baseline_answer_relevance": baseline_relevance,
            })

        rows.append(row)

    return {"testset_path": testset_path, "rows": rows, "include_baseline": include_baseline}


def print_summary(rows: List[Dict[str, Any]], include_baseline: bool) -> None:
    def avg(key):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    print("\n" + "=" * 60)
    print("RAG PIPELINE — SUMMARY")
    print("=" * 60)
    print(f"{'Context Precision':<28} {avg('rag_context_precision')}")
    recall = avg("rag_context_recall")
    print(f"{'Context Recall':<28} {recall if recall is not None else 'N/A (no reference answers)'}")
    print(f"{'Answer Relevance':<28} {avg('rag_answer_relevance')}")
    print(f"{'Faithfulness':<28} {avg('rag_faithfulness')}")
    print(f"{'Avg Confidence Score':<28} {avg('rag_confidence_score')}")
    print(f"{'Avg Response Time (s)':<28} {avg('rag_response_time_s')}")

    if include_baseline:
        print("\n" + "-" * 60)
        print("RAG vs NO-RAG BASELINE")
        print("-" * 60)
        rag_rel = avg("rag_answer_relevance")
        base_rel = avg("baseline_answer_relevance")
        print(f"{'Answer Relevance (RAG)':<28} {rag_rel}")
        print(f"{'Answer Relevance (No-RAG)':<28} {base_rel}")
        if rag_rel is not None and base_rel is not None:
            delta = round(rag_rel - base_rel, 3)
            verdict = "RAG more relevant" if delta > 0 else ("No-RAG more relevant" if delta < 0 else "Tie")
            print(f"{'Delta':<28} {delta:+.3f}  ({verdict})")
        print(f"{'Avg Response Time (RAG)':<28} {avg('rag_response_time_s')}s")
        print(f"{'Avg Response Time (No-RAG)':<28} {avg('baseline_response_time_s')}s")
    print("=" * 60 + "\n")


def save_reports(result: Dict[str, Any], out_dir: str = "data/eval") -> None:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rows = result["rows"]

    csv_path = os.path.join(out_dir, f"results_{ts}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = os.path.join(out_dir, f"results_{ts}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Saved: {csv_path}")
    print(f"Saved: {json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 3 RAG evaluation harness")
    parser.add_argument(
        "--testset", default="data/eval/sample_testset.json",
        help="Path to test set JSON (default: data/eval/sample_testset.json)"
    )
    parser.add_argument(
        "--no-baseline", action="store_true",
        help="Skip the no-RAG baseline comparison (faster, RAG-only scoring)"
    )
    args = parser.parse_args()

    result = evaluate(args.testset, include_baseline=not args.no_baseline)
    print_summary(result["rows"], result["include_baseline"])
    save_reports(result)