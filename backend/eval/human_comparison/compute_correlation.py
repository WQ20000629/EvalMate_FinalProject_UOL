# ------------------------------------------------------------------
# File: backend/eval/human_comparison/compute_correlation.py
# Purpose: Compares human ratings with scores produced by the evaluation model.
# ------------------------------------------------------------------

"""Compare human ratings with model scores and show the agreement for each dimension."""
# Standard modules load CSV and JSON data and calculate summary statistics.
import csv
import json
import os
import random
import statistics
import sys
from collections import defaultdict

# SciPy calculates rank correlation and Matplotlib creates the comparison chart.
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
RATINGS_CSV = os.path.join(HERE, "ratings.csv")
MODEL_JSON = os.path.join(HERE, "model_runs.json")

# Rubric dimensions to compare and their chart labels
DIMENSIONS = ["relevance", "content_depth", "clarity_structure", "confidence_delivery"]
LABELS = {
    "relevance": "Relevance",
    "content_depth": "Content Depth",
    "clarity_structure": "Clarity & Structure",
    "confidence_delivery": "Confidence Delivery",
}

# Colours used for chart text and backgrounds
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
ACCENT = "#2a78d6"
SURFACE = "#fcfcfb"


def load_human():
    """Load and validate the scores entered by the human rater."""
    # Read the human scores and check that every value is between 1 and 10.
    with open(RATINGS_CSV, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    human, missing = {}, []
    for r in rows:
        scores = {}
        for d in DIMENSIONS:
            raw = (r[d] or "").strip()
            try:
                val = float(raw)
                if not 1 <= val <= 10:
                    raise ValueError
                scores[d] = val
            except ValueError:
                missing.append(f"{r['pair_id']}/{d}")
        human[r["pair_id"]] = scores
    if missing:
        print("ratings.csv still has blank or invalid (not 1-10) cells:")
        print("  " + ", ".join(missing))
        sys.exit(1)
    return human


def load_model():
    """Average the valid model runs for each pair and dimension."""
    # Group repeated model scores by answer pair and rubric dimension.
    with open(MODEL_JSON, encoding="utf-8") as f:
        runs = json.load(f)
    grouped = defaultdict(lambda: defaultdict(list))
    excluded = 0
    for r in runs:
        for d in DIMENSIONS:
            if r[d] == 0:
                excluded += 1
                continue
            grouped[r["pair_id"]][d].append(r[d])
    model = {pid: {d: statistics.mean(v) for d, v in dims.items()} for pid, dims in grouped.items()}
    return model, excluded


def main():
    """Compare human scores with model scores and save a scatter plot."""
    human = load_human()
    model, excluded = load_model()
    pairs = sorted(human)
    print(f"{len(pairs)} pairs rated. {excluded} unparseable model scores (0s) excluded.\n")

    # Calculate correlation, average error, and bias for each dimension.
    stats = {}
    print(f"{'dimension':<22}{'spearman':>10}{'p':>9}{'MAE':>7}{'bias':>7}")
    for d in DIMENSIONS:
        h = [human[p][d] for p in pairs]
        m = [model[p][d] for p in pairs]
        rho, pval = spearmanr(h, m)
        mae = statistics.mean(abs(a - b) for a, b in zip(h, m))
        bias = statistics.mean(b - a for a, b in zip(h, m))
        stats[d] = (h, m, rho, pval, mae, bias)
        print(f"{LABELS[d]:<22}{rho:>10.2f}{pval:>9.3f}{mae:>7.2f}{bias:>+7.2f}")

    # Compare the average of all four dimensions as one overall score.
    h_all = [statistics.mean(human[p][d] for d in DIMENSIONS) for p in pairs]
    m_all = [statistics.mean(model[p][d] for d in DIMENSIONS) for p in pairs]
    rho, pval = spearmanr(h_all, m_all)
    mae = statistics.mean(abs(a - b) for a, b in zip(h_all, m_all))
    bias = statistics.mean(b - a for a, b in zip(h_all, m_all))
    print(f"{'Overall (mean of 4)':<22}{rho:>10.2f}{pval:>9.3f}{mae:>7.2f}{bias:>+7.2f}")
    print("\nbias = model minus human (positive = model scores higher than the human).")

    # Find the five dimensions where the model and human scores disagree most.
    gaps = sorted(
        ((abs(model[p][d] - human[p][d]), p, d, human[p][d], model[p][d]) for p in pairs for d in DIMENSIONS),
        reverse=True,
    )[:5]
    print("\nLargest disagreements:")
    for gap, p, d, hv, mv in gaps:
        print(f"  {p} {LABELS[d]:<20} human={hv:.0f} model={mv:.1f} (gap {gap:.1f})")

    # Plot one human-versus-model scatter chart for each dimension.
    fig, axes = plt.subplots(2, 2, figsize=(9, 8.5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    rng = random.Random(0)
    for ax, d in zip(axes.flat, DIMENSIONS):
        h, m, rho, pval, mae, bias = stats[d]
        ax.set_facecolor(SURFACE)
        ax.plot([0, 10], [0, 10], color="#c3c2b7", linewidth=1.2, linestyle="--", zorder=1)
        hj = [v + rng.uniform(-0.12, 0.12) for v in h]
        ax.scatter(hj, m, s=42, color=ACCENT, alpha=0.85, edgecolor=SURFACE, linewidth=0.8, zorder=2)
        ax.set_xlim(0, 10.5)
        ax.set_ylim(0, 10.5)
        ax.set_xlabel("Human rating", color=INK_SECONDARY, fontsize=9)
        ax.set_ylabel("Model score (mean of runs)", color=INK_SECONDARY, fontsize=9)
        ax.set_title(f"{LABELS[d]}\nSpearman rho={rho:.2f}, MAE={mae:.2f}", color=INK_PRIMARY, fontsize=10.5)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color("#c3c2b7")
        ax.spines["bottom"].set_color("#c3c2b7")
        ax.tick_params(colors="#898781", labelsize=8)
        ax.grid(True, color="#e1e0d9", linewidth=0.8)
        ax.set_axisbelow(True)

    fig.suptitle("Human Ratings vs Model Scores", color=INK_PRIMARY, fontsize=13, y=0.99)
    fig.text(0.5, 0.005, f"n={len(pairs)} answers; dashed line = perfect agreement", ha="center",
             color=INK_SECONDARY, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    out = os.path.join(HERE, "agreement_scatter.png")
    fig.savefig(out, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"\nChart saved to {out}")


if __name__ == "__main__":
    main()
