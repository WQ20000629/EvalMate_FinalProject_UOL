"""
Runs every transcript in texts.csv through the app's SentimentAnalyzer and
writes the predictions to results.json for compute_metrics.py to score.

Usage:
    python run_sentiment.py
"""
import csv
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from app.models.sentiment_analyzer import SentimentAnalyzer

HERE = os.path.dirname(__file__)
TEXTS_CSV = os.path.join(HERE, "texts.csv")
RESULTS_JSON = os.path.join(HERE, "results.json")


def load_rows():
    with open(TEXTS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = load_rows()
    if not rows:
        print("No rows found in texts.csv. Nothing to analyze.")
        return

    print("Loading sentiment model...")
    analyzer = SentimentAnalyzer()

    results = []
    for row in rows:
        text_id = row["text_id"]
        transcript = row["transcript"]

        if not transcript.strip():
            print(f"  [SKIP] {text_id}: transcript is empty")
            continue

        outcome = analyzer.analyze(transcript)
        results.append({
            "text_id": text_id,
            "human_sentiment": row["human_sentiment"].strip().upper(),
            "predicted_label": outcome["label"],
            "confidence": outcome["confidence"],
        })
        print(f"  {text_id}: predicted={outcome['label']} ({outcome['confidence']}) "
              f"human={row['human_sentiment']}")

    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. {len(results)}/{len(rows)} texts analyzed. Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
