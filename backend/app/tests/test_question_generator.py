import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.question_generator import QuestionGenerator


def main():
    print("=== Question Generator Test ===\n")
    print("Paste the job description below.")
    print("When done, type END on a new line and press Enter.\n")

    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)

    job_description = "\n".join(lines).strip()
    if not job_description:
        print("No input provided. Exiting.")
        return

    print("\nConnecting to Ollama and generating questions...")
    generator = QuestionGenerator(model="llama3.2:3b")
    questions = generator.generate(job_description, num_questions=3)

    print("\n--- GENERATED QUESTIONS ---")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")


if __name__ == "__main__":
    main()
