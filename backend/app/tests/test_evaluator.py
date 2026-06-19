import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.evaluator import Evaluator


def main():
    print("=== Evaluator Test ===\n")

    question = input("Enter the interview question: ").strip()
    print("Enter the candidate's answer (type END on a new line when done):\n")

    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)

    answer = "\n".join(lines).strip()
    if not answer:
        print("No answer provided. Exiting.")
        return

    print("\nConnecting to Ollama and evaluating...")
    evaluator = Evaluator(model="llama3.2:3b")
    result = evaluator.evaluate(question, answer)

    print("\n--- EVALUATION RESULT ---\n")

    for dim in ["relevance", "content_depth", "clarity_structure"]:
        label = dim.replace("_", " ").title()
        print(f"{label}")
        print(f"  Score:     {result[dim]['score']}/10")
        print(f"  Rationale: {result[dim]['rationale']}")
        print()

    print(f"Overall Score: {result['overall_score']}/10")

if __name__ == "__main__":
    main()
