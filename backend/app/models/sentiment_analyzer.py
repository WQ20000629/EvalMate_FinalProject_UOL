from transformers import pipeline


class SentimentAnalyzer:
    tone_labels = {
        "LABEL_0": "NEGATIVE",
        "LABEL_1": "NEUTRAL",
        "LABEL_2": "POSITIVE",
        "negative": "NEGATIVE",
        "neutral":  "NEUTRAL",
        "positive": "POSITIVE",
    }

    def __init__(self, model="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.hf_model = model
        self.classifier = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=model,
        )

    def analyze(self, text):
        if not text or not text.strip():
            return {"label": "NEUTRAL", "confidence": 0.0}

        output = self.classifier(text, truncation=True, max_length=512)[0]
        raw = output["label"]
        mapped = self.tone_labels.get(raw, raw.upper())

        return {
            "label": mapped,
            "confidence": round(output["score"], 4),
        }
