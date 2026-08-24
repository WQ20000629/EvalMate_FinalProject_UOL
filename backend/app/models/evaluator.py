# Import necessary libraries
import requests
import re

class Evaluator:
    """
    Handles answer evaluation by sending the interview question and candidate response
    to the Ollama model, then parsing the returned scores and rationales into a
    structured format.
    """
    def __init__(self, model="llama3.2:3b", host="http://localhost:11434"):
        """
        Initialise the evaluator with the Ollama model name and host URL.
        """
        self.llm_model = model
        self.endpoint = f"{host}/api/generate"

    def evaluate(self, question, answer, question_type="General"):
        """
        Evaluate a candidate's answer across multiple interview dimensions.
        For behavioural questions, extra instructions are added so that
        clarity and structure are judged based on the STAR method.
        Returns:
            dict: Parsed evaluation results containing scores and rationales
                  for relevance, content depth, clarity structure, confidence delivery,
                  and overall score.

        """
        is_behavioural = question_type.lower() == "behavioural"

        star_note = ""
        if is_behavioural:
            star_note = (
                f"\nIMPORTANT for Clarity Structure Score: This is a Behavioural question. "
                f"You MUST evaluate whether the answer follows the STAR method "
                f"(Situation, Task, Action, Result). "
                f"If the answer does NOT follow STAR, rate Clarity Structure no higher than 4/10. "
                f"The Clarity Structure Rationale MUST explicitly state which STAR components "
                f"were present and which were missing.\n"
            )

        prompt = (
            f"You are an expert interview evaluator.\n"
            f"Evaluate the candidate's answer using the dimensions below.\n\n"
            f"For Confidence Delivery, focus on language use:\n"
            f"- Low confidence: 'I think', 'maybe', 'probably', 'I'm not sure', 'kind of', 'I guess'\n"
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

        res = requests.post(self.endpoint, json=body, timeout=60)
        res.raise_for_status()

        raw = res.json().get("response", "").strip()
        return self._parse_scores(raw)

    def _parse_scores(self, raw):
        """
        Extract scores and rationales from the raw text returned by the model.
        Returns:
            dict: Structured evaluation result with dimension scores, rationales,
                  and an automatically calculated overall score.
        """

        parsed = {
            "relevance":           {"score": None, "rationale": ""},
            "content_depth":       {"score": None, "rationale": ""},
            "clarity_structure":   {"score": None, "rationale": ""},
            "confidence_delivery": {"score": None, "rationale": ""},
            "overall_score":       None,
        }

        matchers = {
            "rel_score":   re.compile(r"Relevance Score:\s*(\d+)", re.IGNORECASE),
            "rel_reason":  re.compile(r"Relevance Rationale:\s*(.+)", re.IGNORECASE),
            "dep_score":   re.compile(r"Content Depth Score:\s*(\d+)", re.IGNORECASE),
            "dep_reason":  re.compile(r"Content Depth Rationale:\s*(.+)", re.IGNORECASE),
            "clar_score":  re.compile(r"Clarity Structure Score:\s*(\d+)", re.IGNORECASE),
            "clar_reason": re.compile(r"Clarity Structure Rationale:\s*(.+)", re.IGNORECASE),
            "conf_score":  re.compile(r"Confidence Delivery Score:\s*(\d+)", re.IGNORECASE),
            "conf_reason": re.compile(r"Confidence Delivery Rationale:\s*(.+)", re.IGNORECASE),
        }

        for row in raw.splitlines():
            row = row.strip()
            if not row:
                continue
            for tag, pattern in matchers.items():
                hit = pattern.match(row)
                if hit:
                    val = hit.group(1).strip()
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

        all_scores = [
            parsed["relevance"]["score"],
            parsed["content_depth"]["score"],
            parsed["clarity_structure"]["score"],
            parsed["confidence_delivery"]["score"],
        ]
        valid = [s for s in all_scores if s is not None]
        if valid:
            parsed["overall_score"] = round(sum(valid) / len(valid), 1)

        for dim in ["relevance", "content_depth", "clarity_structure", "confidence_delivery"]:
            if parsed[dim]["score"] is None:
                parsed[dim]["score"] = 0
                parsed[dim]["rationale"] = "Could not parse evaluation."

        return parsed
