# ------------------------------------------------------------------
# File: backend/eval/sentiment/run_sentiment.py
# Purpose: Runs sentiment analysis on test transcripts and saves predictions.
# ------------------------------------------------------------------

"""Run the sentiment model across all texts and save the predictions for scoring."""
# Standard modules load the text dataset and save predictions.
import csv
import json
import os
import sys

# Import the same sentiment model used by the application.
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from app.models.sentiment_analyzer import SentimentAnalyzer

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
TEXTS_CSV = os.path.join(HERE, "texts.csv")
RESULTS_JSON = os.path.join(HERE, "results.json")


def load_rows():
    """Load the transcripts and their human sentiment labels."""
    with open(TEXTS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    """Run sentiment analysis on every non-empty transcript."""
    rows = load_rows()
    if not rows:
        print("No rows found in texts.csv. Nothing to analyze.")
        return

    print("Loading sentiment model...")
    analyzer = SentimentAnalyzer()

    # Store the human label and model prediction for each transcript.
    results = []
    for row in rows:
        text_id = row["text_id"]
        transcript = row["transcript"]

        if not transcript.strip():
            print(f"  [SKIP] {text_id}: transcript is empty")
            continue

        # Analyse the transcript with the application sentiment model.
        outcome = analyzer.analyze(transcript)
        results.append({
            "text_id": text_id,
            "human_sentiment": row["human_sentiment"].strip().upper(),
            "predicted_label": outcome["label"],
            "confidence": outcome["confidence"],
        })
        print(f"  {text_id}: predicted={outcome['label']} ({outcome['confidence']}) "
              f"human={row['human_sentiment']}")

    # Save predictions for compute_metrics.py and plot_confusion_matrix.py.
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. {len(results)}/{len(rows)} texts analyzed. Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
