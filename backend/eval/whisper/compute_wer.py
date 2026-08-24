"""
Scores a run_whisper.py output against ground_truth.csv using Word Error Rate.

Text is normalized before comparison (lowercased, punctuation stripped, common
contractions expanded) via jiwer's standard transform, so trivial casing/
punctuation differences don't count as transcription errors.

Usage:
    python compute_wer.py                  # scores results_base.json
    python compute_wer.py --model-size small
"""
import argparse
import csv
import json
import os
import statistics
import sys

import jiwer

HERE = os.path.dirname(__file__)
GROUND_TRUTH_CSV = os.path.join(HERE, "ground_truth.csv")


def load_ground_truth():
    with open(GROUND_TRUTH_CSV, newline="", encoding="utf-8") as f:
        return {row["clip_id"]: row for row in csv.DictReader(f)}


def load_results(model_size):
    results_path = os.path.join(HERE, f"results_{model_size}.json")
    if not os.path.exists(results_path):
        print(f"No results file at {results_path}. Run run_whisper.py --model-size {model_size} first.")
        sys.exit(1)
    with open(results_path, encoding="utf-8") as f:
        return json.load(f)


def clip_wer(ground_truth_text, hypothesis_text):
    return jiwer.wer(
        ground_truth_text,
        hypothesis_text,
        reference_transform=jiwer.wer_standardize,
        hypothesis_transform=jiwer.wer_standardize,
    )


def average(values):
    return round(sum(values) / len(values), 3) if values else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-size", default="base", help="Which results_<model-size>.json to score")
    args = parser.parse_args()

    ground_truth = load_ground_truth()
    results = load_results(args.model_size)

    scored = []
    for row in results:
        clip_id = row["clip_id"]
        gt_row = ground_truth.get(clip_id)
        if gt_row is None:
            print(f"  [SKIP] {clip_id}: no ground truth row found")
            continue
        gt_text = gt_row["ground_truth_transcript"]
        if not gt_text.strip():
            print(f"  [SKIP] {clip_id}: ground_truth_transcript is empty")
            continue

        wer = clip_wer(gt_text, row["whisper_transcript"])
        scored.append({
            "clip_id": clip_id,
            "condition": row["condition"],
            "length": row["length"],
            "wer": round(wer, 3),
            "transcribe_seconds": row.get("transcribe_seconds"),
        })

    if not scored:
        print("No clips could be scored. Check ground_truth.csv has transcripts filled in.")
        return

    print(f"\n{'clip_id':<20}{'condition':<12}{'length':<8}{'WER':<8}")
    for r in scored:
        print(f"{r['clip_id']:<20}{r['condition']:<12}{r['length']:<8}{r['wer']:<8}")

    overall = average([r["wer"] for r in scored])
    print(f"\nOverall average WER ({len(scored)} clips): {overall}")

    print("\nBy condition:")
    conditions = sorted(set(r["condition"] for r in scored))
    for cond in conditions:
        vals = [r["wer"] for r in scored if r["condition"] == cond]
        print(f"  {cond:<12} avg WER: {average(vals):<8} (n={len(vals)})")

    print("\nBy length:")
    lengths = sorted(set(r["length"] for r in scored))
    for length in lengths:
        vals = [r["wer"] for r in scored if r["length"] == length]
        print(f"  {length:<12} avg WER: {average(vals):<8} (n={len(vals)})")

    if len(scored) > 1:
        wers = [r["wer"] for r in scored]
        print(f"\nWER std dev across clips: {round(statistics.stdev(wers), 3)}")

    report_path = os.path.join(HERE, f"wer_report_{args.model_size}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "model_size": args.model_size,
            "overall_avg_wer": overall,
            "per_clip": scored,
        }, f, indent=2)
    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    main()
