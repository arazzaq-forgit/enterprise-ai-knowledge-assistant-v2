"""
Diagnostic: print actual cosine similarity scores between each test
question and its retrieved chunks, so relevance_threshold in
ragas_metrics.py can be calibrated against real numbers instead of a
guessed default (0.35).

USAGE:
    python scripts/calibrate_threshold.py --testset data/sample_testset.json

For each question, shows every retrieved chunk's similarity score and a
snippet of its content, so you can visually judge: "yes this chunk is
relevant" vs "no it isn't" — then compare that judgment against the
score to pick a threshold that actually separates the two groups.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.rag_pipeline import RAGPipeline
from src.evaluation.ragas_metrics import cosine_similarity


def main(testset_path: str):
    print("Loading pipeline...")
    pipeline = RAGPipeline()

    with open(testset_path, "r", encoding="utf-8") as f:
        testset = json.load(f)

    all_scores = []

    for item in testset:
        question = item["question"]
        print(f"\n{'=' * 70}")
        print(f"Q: {question}")
        print('=' * 70)

        chunks = pipeline.retriever.retrieve(question)
        q_vec = pipeline.embedding_model.embed_text(question)

        for i, c in enumerate(chunks, 1):
            content = (c.get("content") or "")[:1000]
            c_vec = pipeline.embedding_model.embed_text(content)
            score = cosine_similarity(q_vec, c_vec)
            all_scores.append(score)

            snippet = (c.get("content") or "")[:120].replace("\n", " ")
            print(f"  [{i}] score={score:.3f}  \"{snippet}...\"")

    if all_scores:
        all_scores.sort()
        print(f"\n{'=' * 70}")
        print("SCORE DISTRIBUTION (all chunks, all questions)")
        print('=' * 70)
        print(f"  min:    {min(all_scores):.3f}")
        print(f"  max:    {max(all_scores):.3f}")
        print(f"  median: {all_scores[len(all_scores)//2]:.3f}")
        print(f"  mean:   {sum(all_scores)/len(all_scores):.3f}")
        print(
            "\nLook at the scores above next to each chunk's content.\n"
            "Pick a threshold value that sits between the scores you'd call\n"
            "'relevant' and the scores you'd call 'not relevant'. Update\n"
            "relevance_threshold in RagasLiteMetrics(...) in evaluate_pipeline.py\n"
            "to that value."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--testset", default="data/sample_testset.json")
    args = parser.parse_args()
    main(args.testset)