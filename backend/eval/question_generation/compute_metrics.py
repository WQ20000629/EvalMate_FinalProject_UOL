# ------------------------------------------------------------------
# File: backend/eval/question_generation/compute_metrics.py
# Purpose: Measures question completion, type validity, and type diversity.
# ------------------------------------------------------------------

"""Score the generated questions and show how well the question types were produced."""
# Standard modules load the saved generation results and classify question text.
import json
import os
import re

# Plotting creates the question-type distribution chart.
import matplotlib.pyplot as plt

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
RESULTS_JSON = os.path.join(HERE, "results.json")

# The four real question types, plus General for unparsed questions
REAL_TYPES = ["Behavioural", "Situational", "Motivational", "Technical"]
ALL_TYPES = REAL_TYPES + ["General"]

# One colour per question type. General is grey because it only appears
# when the type could not be parsed.
TYPE_COLORS = {
    "Behavioural": "#2a78d6",
    "Situational": "#eb6834",
    "Motivational": "#1baf7a",
    "Technical": "#eda100",
    "General": "#b6b3ab",
}

# Colours used for chart text and backgrounds
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"

# Matches questions that wrongly start with "Question:"
QUESTION_PREFIX_RE =re.compile(r"^question\s*:\s*", re.IGNORECASE)


def main():
    """Calculate question-generation metrics and save the distribution chart."""
    # Load all generated questions and their requested counts.
    with open(RESULTS_JSON, encoding="utf-8") as f:
        results = json.load(f)

    total_requested = sum(r["requested"] for r in results)
    total_returned = sum(r["returned_count"] for r in results)
    completion_rate = total_returned / total_requested if total_requested else 0

    all_questions = [q for r in results for q in r["questions"]]
    general_count = sum(1 for q in all_questions if q["type"] == "General")
    type_validity_rate = 1 - (general_count / len(all_questions)) if all_questions else 0

    prefix_leaks = sum(1 for q in all_questions if QUESTION_PREFIX_RE.match(q["question"]))
    prefix_leak_rate = prefix_leaks / len(all_questions) if all_questions else 0

    print(f"Total questions requested: {total_requested}")
    print(f"Total questions returned:  {total_returned}")
    print(f"Completion rate:           {completion_rate * 100:.1f}%")
    print(f"Type validity rate:        {type_validity_rate * 100:.1f}% (non-'General')")
    print(f"Redundant 'Question:' prefix rate: {prefix_leak_rate * 100:.1f}% ({prefix_leaks}/{len(all_questions)})")

    # Count question types and measure diversity for each job description.
    jd_files = sorted(set(r["jd_file"] for r in results))
    jd_type_counts = {jd: {t: 0 for t in ALL_TYPES} for jd in jd_files}

    for r in results:
        for q in r["questions"]:
            jd_type_counts[r["jd_file"]][q["type"]] = jd_type_counts[r["jd_file"]].get(q["type"], 0) + 1

    print("\nPer-JD type distribution (across 3 runs) and diversity:")
    for jd in jd_files:
        counts = jd_type_counts[jd]
        diversity = sum(1 for t in REAL_TYPES if counts.get(t, 0) > 0)
        breakdown = ", ".join(f"{t}={counts.get(t, 0)}" for t in ALL_TYPES if counts.get(t, 0) > 0)
        print(f"  {jd:12s} diversity={diversity}/4  ({breakdown})")

    # Create a stacked chart showing the type distribution for each JD.
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    x = range(len(jd_files))
    bottoms = [0] * len(jd_files)
    for t in ALL_TYPES:
        heights = [jd_type_counts[jd].get(t, 0) for jd in jd_files]
        ax.bar(x, heights, bottom=bottoms, width=0.6, color=TYPE_COLORS[t], label=t)
        bottoms = [b + h for b, h in zip(bottoms, heights)]

    ax.set_xticks(list(x))
    ax.set_xticklabels(jd_files, color=INK_SECONDARY, fontsize=10)
    ax.set_ylabel("Questions generated (3 runs x 3 questions)", color=INK_SECONDARY, fontsize=10)
    ax.set_title("Question Type Distribution per Job Description", color=INK_PRIMARY, fontsize=13, pad=14)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#c3c2b7")
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors="#898781")
    ax.yaxis.grid(True, color="#e1e0d9", linewidth=1)
    ax.set_axisbelow(True)

    legend = ax.legend(title="Type", frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0)
    legend.get_title().set_color(INK_SECONDARY)
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)

    fig.tight_layout()
    out_path = os.path.join(HERE, "type_distribution.png")
    fig.savefig(out_path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"\nChart saved to {out_path}")


if __name__ == "__main__":
    main()
