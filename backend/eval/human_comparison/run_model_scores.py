# ------------------------------------------------------------------
# File: backend/eval/human_comparison/run_model_scores.py
# Purpose: Runs the evaluator on answer pairs for comparison with human ratings.
# ------------------------------------------------------------------

"""Generate the model scores for each answer pair so they can be compared with human ratings."""
# Standard modules load the comparison dataset and save model results.
import argparse
import csv
import json
import os
import sys

# Requests warms up Ollama before the evaluator is used.
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from app.models.evaluator import Evaluator

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
DATASET_CSV = os.path.join(HERE, "dataset.csv")
EXISTING_JSON = os.path.join(HERE, "..", "rubric_scoring", "consistency_results.json")
OUT_JSON = os.path.join(HERE, "model_runs.json")
REPEATS = 5
DIMENSIONS = ["relevance", "content_depth", "clarity_structure", "confidence_delivery"]


def parse_args():
    """Read options for choosing whether old scores can be reused."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="score every dataset row again with the current evaluator prompt",
    )
    return parser.parse_args()


def main():
    """Run the evaluator repeatedly for each answer pair."""
    # Load the questions and answers that will be scored.
    args = parse_args()
    with open(DATASET_CSV, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # Reuse old scores unless a fresh run was requested.
    existing = []
    if not args.fresh and os.path.exists(EXISTING_JSON):
        with open(EXISTING_JSON, encoding="utf-8") as f:
            existing = json.load(f)
    reusable = {r["pair_id"] for r in existing}

    results = [r for r in existing if r["pair_id"] in {row["pair_id"] for row in rows}]
    todo = [row for row in rows if row["pair_id"] not in reusable]
    if args.fresh:
        print("Fresh run selected. Existing scores will not be reused.")
    print(
        f"Reusing existing runs for {len(reusable & {r['pair_id'] for r in rows})} pairs; "
        f"scoring {len(todo)} new pairs."
    )

    if todo:
        evaluator = Evaluator()
        print("Warming up Ollama...")
        try:
            requests.post(
                evaluator.endpoint,
                json={"model": evaluator.llm_model, "prompt": "Say hello.", "stream": False},
                timeout=180,
            )
        except requests.exceptions.RequestException as ex:
            print(f"Warm-up call failed ({ex}); continuing anyway.")

        # Score every pair that was not reused.
        for row in todo:
            for run in range(1, REPEATS + 1):
                scores = evaluator.evaluate(row["question"], row["answer"], row["question_type"])
                # Keep only the scores needed by the comparison script.
                entry = {"pair_id": row["pair_id"], "question_type": row["question_type"], "run": run}
                for dim in DIMENSIONS:
                    entry[dim] = scores[dim]["score"]
                results.append(entry)
                print(f"  {row['pair_id']} run {run}/{REPEATS} done")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} runs to {OUT_JSON}")


if __name__ == "__main__":
    main()
