# ------------------------------------------------------------------
# File: backend/eval/whisper/plot_comparison.py
# Purpose: Creates charts comparing Word Error Rate across Whisper model sizes.
# ------------------------------------------------------------------

"""Create a chart comparing the WER of different Whisper model sizes."""
# Standard modules load report files and create output paths.
import argparse
import json
import os

# Matplotlib draws the comparison charts.
import matplotlib.pyplot as plt

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)

# Colours used for chart text, gridlines, and backgrounds.
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

# Separate colours make the model sizes easy to compare.
MODEL_COLORS = {
    "tiny": "#2a78d6",
    "base": "#eb6834",
    "small": "#1baf7a",
}
# Colour for the single-series overall chart
SINGLE_HUE = "#2a78d6"


def load_report(model_size):
    """Load one saved WER report if it exists."""
    path = os.path.join(HERE, f"wer_report_{model_size}.json")
    if not os.path.exists(path):
        print(f"Skipping '{model_size}': no {os.path.basename(path)} found.")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def style_axes(ax):
    """Apply the shared visual style to a chart."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.tick_params(colors=INK_MUTED, length=0)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=1)
    ax.set_axisbelow(True)
    ax.set_facecolor(SURFACE)


def plot_overall(reports, out_path):
    """Create a chart of the overall WER for each model."""
    models = list(reports.keys())
    values = [reports[m]["overall_avg_wer"] for m in models]

    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    bars = ax.bar(models, values, width=0.5, color=SINGLE_HUE)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.008, f"{val:.3f}",
                 ha="center", va="bottom", color=INK_PRIMARY, fontsize=10, fontweight="bold")

    ax.set_title("Overall Word Error Rate by Whisper Model Size", color=INK_PRIMARY, fontsize=12, pad=14)
    ax.set_ylabel("Word Error Rate (lower is better)", color=INK_SECONDARY, fontsize=10)
    ax.set_ylim(0, max(values) * 1.25)
    style_axes(ax)

    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)
    print(f"Saved {out_path}")


def plot_by_condition(reports, out_path):
    """Create a chart comparing WER by condition and model."""
    models = list(reports.keys())

    # Average the clip scores for every condition and model.
    conditions = sorted({r["condition"] for rep in reports.values() for r in rep["per_clip"]})
    cond_avg = {m: {} for m in models}
    for m, rep in reports.items():
        for cond in conditions:
            vals = [r["wer"] for r in rep["per_clip"] if r["condition"] == cond]
            cond_avg[m][cond] = sum(vals) / len(vals) if vals else 0

    x = range(len(conditions))
    n = len(models)
    group_width = 0.75
    bar_width = group_width / n

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    fig.patch.set_facecolor(SURFACE)

    for i, m in enumerate(models):
        offsets = [xi - group_width / 2 + i * bar_width + bar_width / 2 for xi in x]
        values = [cond_avg[m][c] for c in conditions]
        bars = ax.bar(offsets, values, width=bar_width * 0.9,
                       color=MODEL_COLORS.get(m, SINGLE_HUE), label=m)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 0.008, f"{val:.2f}",
                     ha="center", va="bottom", color=INK_PRIMARY, fontsize=8)

    ax.set_xticks(list(x))
    ax.set_xticklabels(conditions, color=INK_SECONDARY, fontsize=10)
    ax.set_title("Word Error Rate by Recording Condition and Model Size", color=INK_PRIMARY, fontsize=12, pad=14)
    ax.set_ylabel("Word Error Rate (lower is better)", color=INK_SECONDARY, fontsize=10)
    ax.set_ylim(0, max(v for m in cond_avg for v in cond_avg[m].values()) * 1.15)
    style_axes(ax)

    legend = ax.legend(title="Model", frameon=False, loc="upper left",
                        bbox_to_anchor=(1.01, 1.0), borderaxespad=0)
    legend.get_title().set_color(INK_SECONDARY)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    fig.tight_layout()
    fig.savefig(out_path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


def main():
    """Load the requested reports and save both comparison charts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["tiny", "base", "small"])
    args = parser.parse_args()

    # Keep only the model reports that are available.
    reports = {}
    for m in args.models:
        rep = load_report(m)
        if rep is not None:
            reports[m] = rep

    if not reports:
        print("No reports found. Run compute_wer.py for at least one model first.")
        return

    plot_overall(reports, os.path.join(HERE, "chart_overall_wer.png"))
    plot_by_condition(reports, os.path.join(HERE, "chart_wer_by_condition.png"))


if __name__ == "__main__":
    main()
