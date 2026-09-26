# ------------------------------------------------------------------
# File: backend/eval/question_generation/run_question_gen.py
# Purpose: Runs question generation repeatedly for the job description files.
# ------------------------------------------------------------------

"""Run the question generator on each JD file and save the output for evaluation."""
# Standard modules find JD files, save results, and import the project code.
import glob
import json
import os
import sys

# Requests warms up the local Ollama model before the evaluation starts.
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from app.models.question_generator import QuestionGenerator

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
JDS_DIR = os.path.join(HERE, "jds")
NUM_QUESTIONS = 3
REPEATS = 3


def main():
    """Generate questions several times for every job description file."""
    # Find the job descriptions that will be tested.
    jd_files = sorted(glob.glob(os.path.join(JDS_DIR, "jd_*.txt")))
    if not jd_files:
        print(f"No jd_*.txt files found in {JDS_DIR}")
        return

    generator = QuestionGenerator()

    print("Warming up Ollama (first call loads the model into memory, can be slow)...")
    try:
        requests.post(
            generator.endpoint,
            json={"model": generator.llm_model, "prompt": "Say hello.", "stream": False},
            timeout=180,
        )
        print("Model warm.\n")
    except requests.exceptions.RequestException as ex:
        print(f"Warm-up call failed ({ex}); continuing anyway.\n")

    # Store each generation run so the metrics script can analyse it later.
    results = []

    for jd_path in jd_files:
        jd_name = os.path.basename(jd_path)
        with open(jd_path, encoding="utf-8") as f:
            jd_text = f.read().strip()

        if not jd_text:
            print(f"  [SKIP] {jd_name}: empty file")
            continue

        print(f"--- {jd_name} ---")
        # Repeat each JD to check whether the generator behaves consistently.
        for run in range(1, REPEATS + 1):
            print(f"  Run {run}/{REPEATS}...")
            questions = generator.generate(jd_text, num_questions=NUM_QUESTIONS)

            # Count the types returned in this run.
            type_counts = {}
            for q in questions:
                type_counts[q["type"]] = type_counts.get(q["type"], 0) + 1

            results.append({
                "jd_file": jd_name,
                "run": run,
                "requested": NUM_QUESTIONS,
                "returned_count": len(questions),
                "questions": questions,
                "type_counts": type_counts,
                "general_count": type_counts.get("General", 0),
            })

            for q in questions:
                print(f"    [{q['type']}] {q['question'][:80]}")

    out_path = os.path.join(HERE, "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nDone. {len(results)} generation runs logged. Results saved to {out_path}")


if __name__ == "__main__":
    main()
