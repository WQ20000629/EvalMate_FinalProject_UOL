import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.sentiment_analyzer import SentimentAnalyzer


def main():
    print("=== Sentiment Analyzer Test ===\n")
    print("Enter the candidate's answer text (type END on a new line when done):\n")

    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)

    text = "\n".join(lines).strip()
    if not text:
        print("No input provided. Exiting.")
        return

    print("\nLoading Hugging Face model and analyzing sentiment...")
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(text)

    print("\n--- SENTIMENT RESULT ---")
    print(f"Label:      {result['label']}")
    print(f"Confidence: {result['confidence'] * 100:.1f}%")


if __name__ == "__main__":
    main()
