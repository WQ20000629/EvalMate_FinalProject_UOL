# ------------------------------------------------------------------
# File: backend/eval/sentiment/plot_confusion_matrix.py
# Purpose: Creates a confusion matrix chart for the sentiment predictions.
# ------------------------------------------------------------------

"""Create a confusion matrix chart from the sentiment evaluation results."""
# Standard modules load the saved predictions and build output paths.
import json
import os

# Plotting and sklearn create the confusion matrix image.
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
RESULTS_JSON = os.path.join(HERE, "results.json")
LABELS = ["NEGATIVE", "NEUTRAL", "POSITIVE"]

# Colours used for chart text and backgrounds
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
SURFACE = "#fcfcfb"

# Blue colour ramp used for the matrix cells.
SEQUENTIAL_BLUE = ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]


def main():
    """Create and save a sentiment confusion matrix chart."""
    # Load the predictions created by run_sentiment.py.
    with open(RESULTS_JSON, encoding="utf-8") as f:
        results = json.load(f)

    # Prepare the human and predicted labels for sklearn.
    y_true = [r["human_sentiment"] for r in results]
    y_pred = [r["predicted_label"] for r in results]

    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=LABELS)
    report = classification_report(y_true, y_pred, labels=LABELS, zero_division=0, output_dict=True)
    all_perfect = all(report[l]["precision"] == 1.0 and report[l]["recall"] == 1.0 for l in LABELS)

    cmap = LinearSegmentedColormap.from_list("seq_blue", SEQUENTIAL_BLUE)

    fig, ax = plt.subplots(figsize=(6.2, 6.6), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    vmax = max(cm.max(), 1)
    im = ax.imshow(cm, cmap=cmap, vmin=0, vmax=vmax)

    ax.set_xticks(range(len(LABELS)))
    ax.set_yticks(range(len(LABELS)))
    ax.set_xticklabels(LABELS, color=INK_SECONDARY, fontsize=11)
    ax.set_yticklabels(LABELS, color=INK_SECONDARY, fontsize=11)
    ax.set_xlabel("Predicted label", color=INK_SECONDARY, fontsize=11, labelpad=10)
    ax.set_ylabel("Human label", color=INK_SECONDARY, fontsize=11, labelpad=10)

    # Draw thin gaps between the cells using the background colour.
    # ref: https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html
    ax.set_xticks(np.arange(-0.5, len(LABELS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(LABELS), 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=3)
    ax.tick_params(which="minor", length=0)
    ax.tick_params(which="major", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Add the count to each cell in the matrix.
    # ref: https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html
    for i in range(len(LABELS)):
        for j in range(len(LABELS)):
            value = cm[i, j]
            label_color = "#ffffff" if value / vmax > 0.5 else INK_PRIMARY
            ax.text(j, i, str(value), ha="center", va="center",
                     fontsize=20, fontweight="bold", color=label_color)

    fig.suptitle("Sentiment Classification: Confusion Matrix",
                  color=INK_PRIMARY, fontsize=14, fontweight="bold", y=0.98)
    subtitle = f"Overall accuracy: {acc * 100:.1f}%  ({sum(t == p for t, p in zip(y_true, y_pred))}/{len(y_true)})"
    if all_perfect:
        subtitle += "  ·  precision, recall, F1 = 1.00 for all three classes"
    ax.set_title(subtitle, color=INK_SECONDARY, fontsize=10.5, pad=16)

    fig.tight_layout(rect=(0, 0, 1, 0.90))
    out_path = os.path.join(HERE, "confusion_matrix.png")
    fig.savefig(out_path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
