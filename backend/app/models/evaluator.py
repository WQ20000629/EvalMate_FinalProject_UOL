# ------------------------------------------------------------------
# File: backend/app/models/evaluator.py
# Purpose: Sends interview answers to the LLM and parses the returned scores.
# ------------------------------------------------------------------

# Import the libraries needed for the evaluator
import requests
import re

class Evaluator:
    """Send an answer to the LLM and turn the result into a simple score dictionary."""

    def __init__(self, model="llama3.2:3b", host="http://localhost:11434"):
        """Set the model name and Ollama API URL."""
        self.llm_model = model
        self.endpoint = f"{host}/api/generate"

    def evaluate(self, question, answer, question_type="General"):
        """Evaluate one answer across the main interview sections."""
        is_behavioural = question_type.lower() == "behavioural"

        # Behavioural answers get an extra rule so the model checks for the STAR method
        star_note = ""
        if is_behavioural:
            star_note = (
                "\nIMPORTANT for Clarity Structure Score: This is a Behavioural question. "
                "You MUST evaluate whether the answer follows the STAR method "
                "(Situation, Task, Action, Result). "
                "If the answer does NOT follow STAR, rate Clarity Structure no higher than 4/10. "
                "The Clarity Structure Rationale MUST explicitly state which STAR components "
                "were present and which were missing.\n"
            )

        # Ask for a fixed text format so the scores can be read back with regex
        prompt = (
            f"You are an expert interview evaluator.\n"
            f"Evaluate the candidate's answer using the dimensions below.\n\n"
            f"For Confidence Delivery, focus on language use:\n"
            f"- Low confidence: 'I think', 'maybe', 'probably', 'I'm not sure', 'kind of', 'I guess', 'um', 'er'\n"
            f"- High confidence: 'I have', 'I did', 'I built', 'I led', definitive statements\n\n"
            f"Respond in EXACTLY this format, no extra text:\n\n"
            f"Relevance Score: <1-10>\n"
            f"Relevance Rationale: <one or two sentences>\n\n"
            f"Content Depth Score: <1-10>\n"
            f"Content Depth Rationale: <one or two sentences>\n\n"
            f"Clarity Structure Score: <1-10>\n"
            f"Clarity Structure Rationale: <one or two sentences>\n\n"
            f"Confidence Delivery Score: <1-10>\n"
            f"Confidence Delivery Rationale: <one or two sentences citing specific phrases>\n"
            f"{star_note}"
            f"\n---\n"
            f"Question Type: {question_type}\n"
            f"Question: {question}\n"
            f"Answer: {answer}\n"
        )

        body = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": False,
        }

        # Give Ollama enough time to load the model the first time
        res = requests.post(self.endpoint, json=body, timeout=180)
        res.raise_for_status()

        raw = res.json().get("response", "").strip()
        return self._parse_scores(raw)

    def _parse_scores(self, raw):
        """Read the raw LLM response and turn it into score fields."""
        # Start with empty values so missing lines can be detected later
        parsed = {
            "relevance": {"score": None, "rationale": ""},
            "content_depth": {"score": None, "rationale": ""},
            "clarity_structure": {"score": None, "rationale": ""},
            "confidence_delivery": {"score": None, "rationale": ""},
            "overall_score": None,
        }

        # One regex for each line the model is asked to return
        matchers = {
            "rel_score": re.compile(r"Relevance Score:\s*(\d+)", re.IGNORECASE),
            "rel_reason": re.compile(r"Relevance Rationale:\s*(.+)", re.IGNORECASE),
            "dep_score": re.compile(r"Content Depth Score:\s*(\d+)", re.IGNORECASE),
            "dep_reason": re.compile(r"Content Depth Rationale:\s*(.+)", re.IGNORECASE),
            "clar_score": re.compile(r"Clarity Structure Score:\s*(\d+)", re.IGNORECASE),
            "clar_reason": re.compile(r"Clarity Structure Rationale:\s*(.+)", re.IGNORECASE),
            "conf_score": re.compile(r"Confidence Delivery Score:\s*(\d+)", re.IGNORECASE),
            "conf_reason": re.compile(r"Confidence Delivery Rationale:\s*(.+)", re.IGNORECASE),
        }

        # Check every line against every pattern and store what matches
        for row in raw.splitlines():
            row = row.strip()
            if not row:
                continue
            for tag, pattern in matchers.items():
                hit = pattern.match(row)
                if hit:
                    val = hit.group(1).strip()
                    # Scores are clamped to 1-10 in case the model goes out of range
                    if tag == "rel_score":
                        parsed["relevance"]["score"] = max(1, min(10, int(val)))
                    elif tag == "rel_reason":
                        parsed["relevance"]["rationale"] = val
                    elif tag == "dep_score":
                        parsed["content_depth"]["score"] = max(1, min(10, int(val)))
                    elif tag == "dep_reason":
                        parsed["content_depth"]["rationale"] = val
                    elif tag == "clar_score":
                        parsed["clarity_structure"]["score"] = max(1, min(10, int(val)))
                    elif tag == "clar_reason":
                        parsed["clarity_structure"]["rationale"] = val
                    elif tag == "conf_score":
                        parsed["confidence_delivery"]["score"] = max(1, min(10, int(val)))
                    elif tag == "conf_reason":
                        parsed["confidence_delivery"]["rationale"] = val

        # Overall score is the average of the scores that were found
        all_scores = [
            parsed["relevance"]["score"],
            parsed["content_depth"]["score"],
            parsed["clarity_structure"]["score"],
            parsed["confidence_delivery"]["score"],
        ]
        valid = [s for s in all_scores if s is not None]
        if valid:
            parsed["overall_score"] = round(sum(valid) / len(valid), 1)

        # Any score that could not be read is set to 0 with a note
        for dim in ["relevance", "content_depth", "clarity_structure", "confidence_delivery"]:
            if parsed[dim]["score"] is None:
                parsed[dim]["score"] = 0
                parsed[dim]["rationale"] = "Could not parse evaluation."

        return parsed
