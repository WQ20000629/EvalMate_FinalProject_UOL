import requests
import re


class Evaluator:
    """
    Uses a local Ollama model to evaluate a candidate's answer to an interview question.
    Scores on relevance, content_depth, and clarity_structure (each 1-10),
    with a detailed rationale for each dimension.
    """

    def __init__(self, model: str = "llama3.2:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.api_url = f"{host}/api/generate"

    def evaluate(self, question: str, answer: str) -> dict:
        """
        Evaluates a candidate's answer against the interview question.

        Args:
            question: The interview question that was asked.
            answer: The candidate's transcribed answer.

        Returns:
            A dict with keys:
                - relevance (dict):        score (int), rationale (str)
                - content_depth (dict):    score (int), rationale (str)
                - clarity_structure (dict):score (int), rationale (str)
                - overall_score (float):   average of the three scores
        """
        prompt = (
            f"You are an expert interview evaluator.\n"
            f"Evaluate the candidate's answer using THREE dimensions.\n\n"
            f"Respond in EXACTLY this format, no extra text:\n\n"
            f"Relevance Score: <1-10>\n"
            f"Relevance Rationale: <one or two sentences explaining the score>\n\n"
            f"Content Depth Score: <1-10>\n"
            f"Content Depth Rationale: <one or two sentences explaining the score>\n\n"
            f"Clarity Structure Score: <1-10>\n"
            f"Clarity Structure Rationale: <one or two sentences explaining the score>\n\n"
            f"---\n"
            f"Question: {question}\n"
            f"Answer: {answer}\n"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        response = requests.post(self.api_url, json=payload, timeout=60)
        response.raise_for_status()

        raw_text = response.json().get("response", "").strip()
        return self._parse_response(raw_text)

    def _parse_response(self, raw_text: str) -> dict:
        """
        Parses the model output into structured evaluation dimensions.
        Falls back gracefully if the format is unexpected.
        """
        result = {
            "relevance":          {"score": None, "rationale": ""},
            "content_depth":      {"score": None, "rationale": ""},
            "clarity_structure":  {"score": None, "rationale": ""},
            "overall_score":      None,
        }

        patterns = {
            "relevance_score":             re.compile(r"Relevance Score:\s*(\d+)", re.IGNORECASE),
            "relevance_rationale":         re.compile(r"Relevance Rationale:\s*(.+)", re.IGNORECASE),
            "content_depth_score":         re.compile(r"Content Depth Score:\s*(\d+)", re.IGNORECASE),
            "content_depth_rationale":     re.compile(r"Content Depth Rationale:\s*(.+)", re.IGNORECASE),
            "clarity_structure_score":     re.compile(r"Clarity Structure Score:\s*(\d+)", re.IGNORECASE),
            "clarity_structure_rationale": re.compile(r"Clarity Structure Rationale:\s*(.+)", re.IGNORECASE),
        }

        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue

            for key, pattern in patterns.items():
                match = pattern.match(line)
                if match:
                    value = match.group(1).strip()
                    dimension, field = key.rsplit("_", 1) if "_score" not in key.replace("_score", "") else (key[:-6], "score")

                    # Map key to result structure
                    if key == "relevance_score":
                        result["relevance"]["score"] = max(1, min(10, int(value)))
                    elif key == "relevance_rationale":
                        result["relevance"]["rationale"] = value
                    elif key == "content_depth_score":
                        result["content_depth"]["score"] = max(1, min(10, int(value)))
                    elif key == "content_depth_rationale":
                        result["content_depth"]["rationale"] = value
                    elif key == "clarity_structure_score":
                        result["clarity_structure"]["score"] = max(1, min(10, int(value)))
                    elif key == "clarity_structure_rationale":
                        result["clarity_structure"]["rationale"] = value

        # Calculate overall score
        scores = [
            result["relevance"]["score"],
            result["content_depth"]["score"],
            result["clarity_structure"]["score"],
        ]
        valid_scores = [s for s in scores if s is not None]
        if valid_scores:
            result["overall_score"] = round(sum(valid_scores) / len(valid_scores), 1)

        # Fallback for any unparsed dimension
        for dim in ["relevance", "content_depth", "clarity_structure"]:
            if result[dim]["score"] is None:
                result[dim]["score"] = 0
                result[dim]["rationale"] = "Could not parse evaluation."

        return result
