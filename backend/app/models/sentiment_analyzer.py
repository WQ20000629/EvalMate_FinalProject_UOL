from transformers import pipeline


class SentimentAnalyzer:
    """
    Uses a local Hugging Face model to analyze sentiment of a candidate's answer.
    Returns a label (POSITIVE / NEGATIVE) and a confidence score.
    """

    def __init__(self, model: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_name = model
        # Pipeline downloads and caches the model on first run
        self._pipeline = pipeline("sentiment-analysis", model=model)

    def analyze(self, text: str) -> dict:
        """
        Analyzes the sentiment of the given text.

        Args:
            text: The transcribed answer text.

        Returns:
            A dict with keys:
                - label (str):      "POSITIVE" or "NEGATIVE"
                - confidence (float): 0.0 to 1.0
        """
        if not text or not text.strip():
            return {"label": "NEUTRAL", "confidence": 0.0}

        # Truncate to 512 tokens max (model limit)
        result = self._pipeline(text[:512])[0]

        return {
            "label": result["label"],
            "confidence": round(result["score"], 4),
        }
