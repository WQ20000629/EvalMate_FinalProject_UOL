# ------------------------------------------------------------------
# File: backend/eval/gaze/compute_metrics.py
# Purpose: Calculates gaze accuracy metrics and creates the evaluation charts.
# ------------------------------------------------------------------

"""Score the gaze predictions and generate a simple summary plus charts."""
# Standard modules read the saved prediction file and build output paths.
import json
import os

# Plotting and metric libraries calculate scores and create the charts.
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, accuracy_score

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
PREDICTIONS_JSON = os.path.join(HERE, "predictions.json")

# Colours used for chart text and backgrounds
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"
# Blue shades for the confusion matrix cells
BLUE_RAMP = ["#eaf2fc", "#c3ddf7", "#8fc0f0", "#5aa1e6", "#2a78d6", "#1a4f8f"]
# Bar colours for high, medium, and low accuracy
GOOD, WARNING, CRITICAL = "#0ca30c", "#fab219", "#d03b3b"

# Chart labels for each recorded condition, in recording order
CONDITION_LABELS = {
    "camera_1": "Camera (1)",
    "camera_2": "Camera (2)",
    "camera_3": "Camera (3)",
    "camera_4": "Camera (4)",
    "camera_5": "Camera (5)",
    "down": "Looking down",
    "side": "Looking to side",
    "eyes_closed": "Eyes closed",
    "extreme_angle": "Extreme head angle",
}


def main():
    """Calculate gaze metrics and save the two evaluation charts."""
    # Load the frame-level predictions created by run_gaze_eval.py.
    with open(PREDICTIONS_JSON, encoding="utf-8") as f:
        preds = json.load(f)

    # Convert the labels into binary values for sklearn.
    y_true = [1 if p["expected_looking"] else 0 for p in preds]
    y_pred = [1 if p["predicted_looking"] else 0 for p in preds]

    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", pos_label=1, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=[1, 0])  # [ON, OFF] order

    print(f"Frames evaluated: {len(preds)}")
    print(f"Accuracy:  {acc * 100:.1f}%")
    print(f"Precision: {precision:.3f}  (of frames predicted ON, fraction actually ON)")
    print(f"Recall:    {recall:.3f}  (of frames actually ON, fraction predicted ON)")
    print(f"F1:        {f1:.3f}")
    print("\nConfusion matrix (rows=actual, cols=predicted, order=[ON, OFF]):")
    print(cm)

    # Count frames where the face or iris landmarks were unavailable.
    no_face_count = sum(1 for p in preds if not p["face_detected"])
    fallback_count = sum(1 for p in preds if p["face_detected"] and p["landmark_count"] < 474)
    print(f"\nFrames with no face detected: {no_face_count}/{len(preds)}")
    print(f"Frames with iris-refinement fallback (<474 landmarks): {fallback_count}/{len(preds)}")

    # Compare accuracy separately for each recorded gaze condition.
    conditions = sorted(set(p["condition"] for p in preds), key=lambda c: list(CONDITION_LABELS).index(c))
    print("\nPer-condition accuracy:")
    cond_acc = {}
    for cond in conditions:
        rows = [p for p in preds if p["condition"] == cond]
        correct = sum(1 for r in rows if r["correct"])
        cond_acc[cond] = correct / len(rows) if rows else 0
        print(f"  {CONDITION_LABELS[cond]:<22} {correct}/{len(rows)} ({cond_acc[cond] * 100:.1f}%)")

    # Create a heatmap showing the predicted and expected gaze labels.
    # ref: https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html
    fig, ax = plt.subplots(figsize=(5, 5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    cm_norm = cm / cm.sum() if cm.sum() else cm
    im = ax.imshow(cm_norm, cmap=plt.cm.colors.LinearSegmentedColormap.from_list("blues", BLUE_RAMP), vmin=0, vmax=cm_norm.max() or 1)

    labels = ["ON\n(looking)", "OFF\n(not looking)"]
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(labels, color=INK_SECONDARY, fontsize=10)
    ax.set_yticklabels(labels, color=INK_SECONDARY, fontsize=10)
    ax.set_xlabel("Predicted", color=INK_SECONDARY, fontsize=10)
    ax.set_ylabel("Actual (script)", color=INK_SECONDARY, fontsize=10)

    for i in range(2):
        for j in range(2):
            val = cm[i, j]
            text_color = INK_PRIMARY if cm_norm[i, j] < (cm_norm.max() or 1) * 0.6 else "#fcfcfb"
            ax.text(j, i, str(val), ha="center", va="center", fontsize=16, fontweight="bold", color=text_color)

    fig.suptitle("Gaze Detection Confusion Matrix", color=INK_PRIMARY, fontsize=13, y=0.98)
    ax.set_title(f"{len(preds)} frames  |  accuracy={acc * 100:.1f}%", color=INK_SECONDARY, fontsize=10, pad=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    out1 = os.path.join(HERE, "confusion_matrix.png")
    fig.savefig(out1, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"\nChart saved to {out1}")

    # Create a bar chart showing accuracy for each condition.
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    labels2 = [CONDITION_LABELS[c] for c in conditions]
    values = [cond_acc[c] * 100 for c in conditions]
    colors = [GOOD if v >= 80 else WARNING if v >= 50 else CRITICAL for v in values]

    x = np.arange(len(conditions))
    ax.bar(x, values, width=0.6, color=colors)
    for i, v in enumerate(values):
        ax.text(i, v + 2, f"{v:.0f}%", ha="center", fontsize=9, color=INK_PRIMARY, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels2, rotation=30, ha="right", fontsize=9, color=INK_SECONDARY)
    ax.set_ylabel("Accuracy vs. scripted condition", color=INK_SECONDARY, fontsize=10)
    ax.set_ylim(0, 110)
    ax.set_title("Gaze Heuristic Accuracy by Condition", color=INK_PRIMARY, fontsize=13, pad=14)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#c3c2b7")
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors="#898781")
    ax.yaxis.grid(True, color="#e1e0d9", linewidth=1)
    ax.set_axisbelow(True)

    fig.tight_layout()
    out2 = os.path.join(HERE, "accuracy_by_condition.png")
    fig.savefig(out2, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart saved to {out2}")


if __name__ == "__main__":
    main()
