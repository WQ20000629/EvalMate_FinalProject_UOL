"""
Scores run_sentiment.py's results.json against the human_sentiment labels in
texts.csv: overall accuracy, confusion matrix, and per-class precision/recall/F1.

Usage:
    python compute_metrics.py
"""
import json
import os
import sys

from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

HERE = os.path.dirname(__file__)
RESULTS_JSON = os.path.join(HERE, "results.json")
LABELS = ["NEGATIVE", "NEUTRAL", "POSITIVE"]


def main():
    if not os.path.exists(RESULTS_JSON):
        print(f"No results.json found. Run run_sentiment.py first.")
        sys.exit(1)

    with open(RESULTS_JSON, encoding="utf-8") as f:
        results = json.load(f)

    if not results:
        print("results.json is empty.")
        return

    y_true = [r["human_sentiment"] for r in results]
    y_pred = [r["predicted_label"] for r in results]

    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=LABELS)
    report = classification_report(y_true, y_pred, labels=LABELS, zero_division=0, output_dict=True)

    print(f"Overall accuracy: {acc:.3f} ({sum(t == p for t, p in zip(y_true, y_pred))}/{len(y_true)})\n")

    print("Confusion matrix (rows = human label, columns = predicted label):")
    header = "".join(f"{l:>10}" for l in LABELS)
    print(f"{'':>10}{header}")
    for label, row in zip(LABELS, cm):
        print(f"{label:>10}" + "".join(f"{v:>10}" for v in row))

    print("\nPer-class metrics:")
    print(f"{'label':<10}{'precision':>10}{'recall':>10}{'f1':>10}{'support':>10}")
    for label in LABELS:
        m = report[label]
        print(f"{label:<10}{m['precision']:>10.2f}{m['recall']:>10.2f}{m['f1-score']:>10.2f}{m['support']:>10.0f}")

    mismatches = [r for r in results if r["human_sentiment"] != r["predicted_label"]]
    if mismatches:
        print("\nMisclassified:")
        for r in mismatches:
            print(f"  {r['text_id']}: human={r['human_sentiment']} predicted={r['predicted_label']} "
                  f"(confidence {r['confidence']})")


if __name__ == "__main__":
    main()
