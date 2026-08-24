# Import necessary libraries
from transformers import pipeline

class SentimentAnalyzer:
    """
    Performs sentiment (tone) analysis on text using a HuggingFace model.
    The class maps model-specific labels into standardised labels:
    NEGATIVE, NEUTRAL, and POSITIVE, and returns both the label
    and its confidence score.
    """
    # Mapping from model output labels to standardised labels
    tone_labels = {
        "LABEL_0": "NEGATIVE",
        "LABEL_1": "NEUTRAL",
        "LABEL_2": "POSITIVE",
        "negative": "NEGATIVE",
        "neutral":  "NEUTRAL",
        "positive": "POSITIVE",
    }

    def __init__(self, model="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """
        Initialise the sentiment analyzer with a HuggingFace model.
        """
        self.hf_model = model
        self.classifier = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=model,
        )

    def analyze(self, text):
        """
        Analyze the sentiment of a given text input.
        Returns:
            dict: {
                "label": "POSITIVE" / "NEUTRAL" / "NEGATIVE",
                "confidence": float
            }
        """
        if not text or not text.strip():
            return {"label": "NEUTRAL", "confidence": 0.0}

        # Run the model (truncated to avoid overly long inputs)
        output = self.classifier(text, truncation=True, max_length=512)[0]

        # Extract raw label returned by the model
        raw = output["label"]

        # Convert model-specific label into standardised label
        mapped = self.tone_labels.get(raw, raw.upper())

        return {
            "label": mapped,
            "confidence": round(output["score"], 4),
        }
