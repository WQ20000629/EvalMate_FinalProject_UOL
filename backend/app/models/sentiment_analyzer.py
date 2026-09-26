# ------------------------------------------------------------------
# File: backend/app/models/sentiment_analyzer.py
# Purpose: Classifies answer transcripts as positive, neutral, or negative.
# ------------------------------------------------------------------

# Import the Hugging Face library used for sentiment analysis
from transformers import pipeline


class SentimentAnalyzer:
    """Use a Hugging Face model to detect whether text is positive, neutral, or negative."""

    # Map the model labels to the labels used in this app
    # ref: https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest
    tone_labels = {
        "LABEL_0": "NEGATIVE",
        "LABEL_1": "NEUTRAL",
        "LABEL_2": "POSITIVE",
        "negative": "NEGATIVE",
        "neutral": "NEUTRAL",
        "positive": "POSITIVE",
    }

    def __init__(self, model="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """Load the sentiment model."""
        # ref: https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest
        self.hf_model = model
        self.classifier = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=model,
        )

    def analyze(self, text):
        """Return the sentiment label and confidence for a piece of text."""
        if not text or not text.strip():
            return {"label": "NEUTRAL", "confidence": 0.0}

        # Run the model on the text and keep it short enough for memory
        output = self.classifier(text, truncation=True, max_length=512)[0]

        raw = output["label"]
        mapped = self.tone_labels.get(raw, raw.upper())

        return {
            "label": mapped,
            "confidence": round(output["score"], 4),
        }
