# ------------------------------------------------------------------
# File: backend/eval/rubric_scoring/compute_consistency.py
# Purpose: Measures how much evaluator scores change across repeated runs.
# ------------------------------------------------------------------

"""Check how stable the evaluator scores are across repeated runs."""
# Standard modules load results and calculate standard deviations.
import json
import os
import statistics

# Matplotlib creates the consistency summary chart.
import matplotlib.pyplot as plt

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
RESULTS_JSON = os.path.join(HERE, "consistency_results.json")

# Rubric dimensions to check and their chart labels
DIMENSIONS = ["relevance", "content_depth", "clarity_structure", "confidence_delivery"]
DIMENSION_LABELS = {
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


def main():
    """Calculate score variation and save a chart by rubric dimension."""
    # Load the repeated evaluator scores.
    with open(RESULTS_JSON, encoding="utf-8") as f:
        results = json.load(f)

    pair_ids = sorted(set(r["pair_id"] for r in results))

    # Calculate standard deviation for every pair and rubric dimension.
    stdevs = {dim: [] for dim in DIMENSIONS}
    print(f"{'pair_id':<10}" + "".join(f"{DIMENSION_LABELS[d]:>22}" for d in DIMENSIONS))
    for pid in pair_ids:
        runs = [r for r in results if r["pair_id"] == pid]
        row_str = f"{pid:<10}"
        for dim in DIMENSIONS:
            values = [r[dim] for r in runs]
            sd = statistics.stdev(values) if len(values) > 1 else 0.0
            stdevs[dim].append(sd)
            row_str += f"{'std=' + format(sd, '.2f') + ' (' + str(min(values)) + '-' + str(max(values)) + ')':>22}"
        print(row_str)

    # Summarise the average and range of variation for each dimension.
    avg_stdev = {dim: statistics.mean(stdevs[dim]) for dim in DIMENSIONS}
    max_stdev = {dim: max(stdevs[dim]) for dim in DIMENSIONS}
    min_stdev = {dim: min(stdevs[dim]) for dim in DIMENSIONS}

    print("\nAverage std dev across all 10 pairs (lower = more consistent):")
    for dim in DIMENSIONS:
        print(f"  {DIMENSION_LABELS[dim]:<22} avg={avg_stdev[dim]:.2f}  range=[{min_stdev[dim]:.2f}, {max_stdev[dim]:.2f}]")

    # List dimensions where the repeated scores vary by at least one point.
    high_variance = [(pid, dim, sd) for i, pid in enumerate(pair_ids) for dim in DIMENSIONS
                     if (sd := stdevs[dim][i]) >= 1.0]
    if high_variance:
        print("\nPairs with high variance (std dev >= 1.0):")
        for pid, dim, sd in high_variance:
            print(f"  {pid} / {DIMENSION_LABELS[dim]}: std={sd:.2f}")

    # Plot average variation with the minimum and maximum as error bars.
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    labels = [DIMENSION_LABELS[d] for d in DIMENSIONS]
    means = [avg_stdev[d] for d in DIMENSIONS]
    err_low = [avg_stdev[d] - min_stdev[d] for d in DIMENSIONS]
    err_high = [max_stdev[d] - avg_stdev[d] for d in DIMENSIONS]

    x = range(len(DIMENSIONS))
    ax.bar(x, means, width=0.55, color=ACCENT, yerr=[err_low, err_high], capsize=5,
           error_kw={"ecolor": INK_SECONDARY, "elinewidth": 1.2})

    for i, m in enumerate(means):
        ax.text(i, m + err_high[i] + 0.05, f"{m:.2f}", ha="center", fontsize=10, color=INK_PRIMARY, fontweight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10, color=INK_SECONDARY)
    ax.set_ylabel("Std. dev. across 5 identical repeats (0-10 scale)", color=INK_SECONDARY, fontsize=10)
    ax.set_title("Evaluator Score Consistency by Dimension", color=INK_PRIMARY, fontsize=13, pad=14)
    ax.set_ylim(0, max(max_stdev.values()) * 1.3 + 0.3)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#c3c2b7")
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors="#898781")
    ax.yaxis.grid(True, color="#e1e0d9", linewidth=1)
    ax.set_axisbelow(True)

    fig.tight_layout()
    out_path = os.path.join(HERE, "consistency_by_dimension.png")
    fig.savefig(out_path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"\nChart saved to {out_path}")


if __name__ == "__main__":
    main()
