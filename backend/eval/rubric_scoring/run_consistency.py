# ------------------------------------------------------------------
# File: backend/eval/rubric_scoring/run_consistency.py
# Purpose: Runs rubric examples repeatedly to test evaluator consistency.
# ------------------------------------------------------------------

"""Run the evaluator multiple times on the same inputs to test how stable the scores are."""
# Standard modules load the rubric dataset and save repeated results.
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
REPEATS = 5
DIMENSIONS = ["relevance", "content_depth", "clarity_structure", "confidence_delivery"]


def load_dataset():
    """Load the question and answer pairs used for the consistency test."""
    with open(DATASET_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    """Run the evaluator five times for every rubric test pair."""
    rows = load_dataset()
    if not rows:
        print("No rows found in dataset.csv.")
        return

    evaluator = Evaluator()

    print("Warming up Ollama...")
    try:
        requests.post(
            evaluator.endpoint,
            json={"model": evaluator.llm_model, "prompt": "Say hello.", "stream": False},
            timeout=180,
        )
        print("Model warm.\n")
    except requests.exceptions.RequestException as ex:
        print(f"Warm-up call failed ({ex}); continuing anyway.\n")

    # Store all repeated scores before writing the results file.
    results = []
    for row in rows:
        pair_id = row["pair_id"]
        print(f"--- {pair_id} ({row['question_type']}) ---")

        # Repeat the same input to measure prompt and model variation.
        for run in range(1, REPEATS + 1):
            scores = evaluator.evaluate(row["question"], row["answer"], row["question_type"])
            # Save one compact result row for this run.
            entry = {
                "pair_id": pair_id,
                "question_type": row["question_type"],
                "run": run,
            }
            for dim in DIMENSIONS:
                entry[dim] = scores[dim]["score"]
            results.append(entry)
            print(f"  Run {run}/{REPEATS}: " + " ".join(f"{dim}={entry[dim]}" for dim in DIMENSIONS))

    out_path = os.path.join(HERE, "consistency_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nDone. {len(results)} evaluation runs logged. Results saved to {out_path}")


if __name__ == "__main__":
    main()
