import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.question_generator import QuestionGenerator
from app.models.transcriber import Transcriber
from app.models.evaluator import Evaluator
from app.models.sentiment_analyzer import SentimentAnalyzer


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

    # --- Step 1: Load models ---
    print("\n[1/4] Loading models...")
    question_generator = QuestionGenerator(model="llama3.2:3b")
    transcriber = Transcriber(model_size="base")
    evaluator = Evaluator(model="llama3.2:3b")
    sentiment_analyzer = SentimentAnalyzer()
    print("      All models loaded.\n")

    # --- Step 2: Generate questions from JD ---
    job_description = get_multiline_input("[2/4] Paste the Job Description:")
    if not job_description:
        print("No JD provided. Exiting.")
        return

    print("\nGenerating questions from JD...")
    questions = question_generator.generate(job_description, num_questions=3)

    print("\n--- GENERATED QUESTIONS ---")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")

    # --- Step 3: Per-question loop ---
    print("\n[3/4] Answer each question.\n")

    results = []

    for i, question in enumerate(questions, 1):
        print("-" * 50)
        print(f"Question {i}: {question}\n")

        audio_path = input("Enter path to your audio answer file: ").strip()
        if not os.path.exists(audio_path):
            print(f"File not found: {audio_path}. Skipping question {i}.")
            continue

        print("  Transcribing...")
        transcript = transcriber.transcribe(audio_path)
        print(f"  Transcript: {transcript}\n")

        print("  Evaluating...")
        evaluation = evaluator.evaluate(question, transcript)

        print("  Analyzing sentiment...")
        sentiment = sentiment_analyzer.analyze(transcript)

        results.append({
            "question": question,
            "transcript": transcript,
            "evaluation": evaluation,
            "sentiment": sentiment,
        })

        print(f"  Done. Overall score: {evaluation['overall_score']}/10 | "
              f"Sentiment: {sentiment['label']} ({sentiment['confidence'] * 100:.1f}%)")

    # --- Step 4: Final report ---
    print("\n" + "=" * 50)
    print("   FINAL REPORT")
    print("=" * 50)

    if not results:
        print("No answers were recorded.")
        return

    total_relevance = 0
    total_content_depth = 0
    total_clarity_structure = 0
    total_overall = 0
    sentiment_labels = []

    for i, r in enumerate(results, 1):
        ev = r["evaluation"]
        se = r["sentiment"]

        print(f"\nQ{i}: {r['question']}")
        print(f"  Transcript: {r['transcript']}")
        print(f"\n  Relevance          — {ev['relevance']['score']}/10")
        print(f"    Rationale: {ev['relevance']['rationale']}")
        print(f"  Content Depth      — {ev['content_depth']['score']}/10")
        print(f"    Rationale: {ev['content_depth']['rationale']}")
        print(f"  Clarity/Structure  — {ev['clarity_structure']['score']}/10")
        print(f"    Rationale: {ev['clarity_structure']['rationale']}")
        print(f"\n  Overall Score:  {ev['overall_score']}/10")
        print(f"  Sentiment:      {se['label']} ({se['confidence'] * 100:.1f}%)")

        total_relevance += ev["relevance"]["score"]
        total_content_depth += ev["content_depth"]["score"]
        total_clarity_structure += ev["clarity_structure"]["score"]
        total_overall += ev["overall_score"]
        sentiment_labels.append(se["label"])

    n = len(results)
    avg_relevance = round(total_relevance / n, 1)
    avg_content_depth = round(total_content_depth / n, 1)
    avg_clarity_structure = round(total_clarity_structure / n, 1)
    avg_overall = round(total_overall / n, 1)
    dominant_sentiment = max(set(sentiment_labels), key=sentiment_labels.count)

    print("\n" + "=" * 50)
    print("   AGGREGATED SCORES")
    print("=" * 50)
    print(f"  Avg Relevance:          {avg_relevance}/10")
    print(f"  Avg Content Depth:      {avg_content_depth}/10")
    print(f"  Avg Clarity/Structure:  {avg_clarity_structure}/10")
    print(f"  ─────────────────────────────")
    print(f"  Final Overall Score:    {avg_overall}/10")
    print(f"  Dominant Sentiment:     {dominant_sentiment}")
    print("=" * 50)


if __name__ == "__main__":
    main()
