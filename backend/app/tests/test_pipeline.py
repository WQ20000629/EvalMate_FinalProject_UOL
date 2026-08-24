import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.pipeline import InterviewPipeline

def get_multiline_input(prompt: str) -> str:
    print(prompt)
    print("(Type END on a new line when done)\n")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def main():
    print("=" * 50)
    print("   AI INTERVIEW EVALUATOR — PIPELINE TEST")
    print("=" * 50)

    print("\n[1/4] Loading pipeline...")
    pipeline = InterviewPipeline()
    print("      Ready.\n")

    job_description = get_multiline_input("[2/4] Paste the Job Description:")
    if not job_description:
        print("No JD provided. Exiting.")
        return

    print("\nGenerating questions...")
    questions = pipeline.generate_questions(job_description)

    print("\n--- GENERATED QUESTIONS ---")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")

    print("\n[3/4] Answer each question.\n")
    results = []

    for i, question in enumerate(questions, 1):
        print("-" * 50)
        print(f"Question {i}: {question}\n")

        audio_path = input("Enter path to your audio answer file: ").strip()
        if not os.path.exists(audio_path):
            print(f"File not found: {audio_path}. Skipping.\n")
            continue

        print("  Processing...")
        result = pipeline.process_answer(question, audio_path)
        results.append(result)

        ev = result["evaluation"]
        se = result["sentiment"]
        print(f"  Transcript: {result['transcript']}")
        print(f"  Overall Score: {ev['overall_score']}/10 | "
              f"Sentiment: {se['label']} ({se['confidence'] * 100:.1f}%)\n")

    print("\n" + "=" * 50)
    print("   FINAL REPORT")
    print("=" * 50)

    if not results:
        print("No answers recorded.")
        return

    for i, r in enumerate(results, 1):
        ev = r["evaluation"]
        se = r["sentiment"]
        print(f"\nQ{i}: {r['question']}")
        print(f"  Transcript: {r['transcript']}")
        print(f"\n  Relevance           — {ev['relevance']['score']}/10")
        print(f"    Rationale: {ev['relevance']['rationale']}")
        print(f"  Content Depth       — {ev['content_depth']['score']}/10")
        print(f"    Rationale: {ev['content_depth']['rationale']}")
        print(f"  Clarity/Structure   — {ev['clarity_structure']['score']}/10")
        print(f"    Rationale: {ev['clarity_structure']['rationale']}")
        print(f"  Confidence Delivery — {ev['confidence_delivery']['score']}/10")
        print(f"    Rationale: {ev['confidence_delivery']['rationale']}")
        print(f"\n  Overall Score: {ev['overall_score']}/10")
        print(f"  Sentiment:     {se['label']} ({se['confidence'] * 100:.1f}%)")

    summary = pipeline.aggregate_results(results)

    print("\n" + "=" * 50)
    print("   AGGREGATED SCORES")
    print("=" * 50)
    print(f"  Avg Relevance:            {summary['avg_relevance']}/10")
    print(f"  Avg Content Depth:        {summary['avg_content_depth']}/10")
    print(f"  Avg Clarity/Structure:    {summary['avg_clarity_structure']}/10")
    print(f"  Avg Confidence Delivery:  {summary['avg_confidence_delivery']}/10")
    print(f"  ─────────────────────────────")
    print(f"  Final Overall Score:      {summary['final_overall_score']}/10")
    print(f"  Dominant Sentiment:       {summary['dominant_sentiment']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
