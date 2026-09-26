# ------------------------------------------------------------------
# File: backend/app/models/question_generator.py
# Purpose: Generates interview questions from a job description using the LLM.
# ------------------------------------------------------------------

# Import the libraries needed for question generation
import requests
import re

class QuestionGenerator:
    """Generate interview questions from a job description using the Ollama model."""

    accepted_types = {"behavioural", "situational", "motivational", "technical"}

    def __init__(self, model="llama3.2:3b", host="http://localhost:11434"):
        """Set the model name and Ollama URL."""
        self.llm_model = model
        self.endpoint = f"{host}/api/generate"

    def generate(self, jd_text, num_questions=3, allowed_types=None):
        """Generate a list of interview questions from the job description."""
        # Use every question type if the user did not pick any
        types_to_use = allowed_types if allowed_types else ["Behavioural", "Situational", "Motivational", "Technical"]
        accepted_this_call = {t.lower() for t in types_to_use}
        types_str = ", ".join(types_to_use)

        # Ask for a mix of types only when more than one type is allowed
        mix_rule = (
            f"- Use a mix of question types across the {num_questions} questions.\n"
            if len(types_to_use) > 1
            else f"- Every question must be of type {types_to_use[0]}.\n"
        )
        # Show the exact numbered format for the model to copy
        example_lines ="".join(f"  {i}. [Type] Question text\n" for i in range(1, num_questions + 1))

        prompt = (
            f"You are an expert interviewer. Based on the job description below, "
            f"generate exactly {num_questions} interview questions.\n\n"
            f"Each question must be one of these types: {types_str}.\n\n"
            f"Rules:\n"
            f"{mix_rule}"
            f"- Output ONLY in this exact format, nothing else:\n"
            f"{example_lines}"
            f"- No explanations, no headers, no extra text.\n\n"
            f"Job Description:\n{jd_text}\n\n"
            f"Questions:"
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
        return self._extract_questions(raw, num_questions, accepted_this_call)

    def _extract_questions(self, raw, limit, accepted_types=None):
        """Read the raw text output and turn it into a list of question dictionaries."""
        accepted = accepted_types if accepted_types else self.accepted_types
        found = []

        # Match lines like 1. [Technical] What is ...?
        bracketed = re.compile(r"^\d+[\.\)]\s*\[(\w+)\]\s*(.+)$", re.IGNORECASE)

        # Match lines like 1. Technical What is ...?
        unbracketed = re.compile(
            r"^\d+[\.\)]\s*(behavioural|situational|motivational|technical)\s+(.+)$",
            re.IGNORECASE
        )

        for row in raw.splitlines():
            row = row.strip()
            if not row:
                continue

            hit = bracketed.match(row) or unbracketed.match(row)
            if hit:
                qtype = hit.group(1).strip().capitalize()
                qtext = hit.group(2).strip()

                # Label any type the user did not ask for as General
                if qtype.lower() not in accepted:
                    qtype = "General"
                found.append({"question": qtext, "type": qtype})
            if len(found) >= limit:
                break

        # Fallback parsing if the model did not follow the exact output format
        if not found:
            for row in raw.splitlines():
                row = row.strip()
                if row and row[0].isdigit():
                    # Remove the number at the start, e.g. "1." or "2)"
                    for sep in [".", ")", ":"]:
                        if sep in row[:3]:
                            row = row.split(sep, 1)[-1].strip()
                            break
                    detected_type = "General"

                    # Take the type from the start of the line if there is one
                    for t in accepted:
                        if row.lower().startswith(t):
                            detected_type = t.capitalize()
                            row = row[len(t):].strip()
                            break
                    if row:
                        found.append({"question": row, "type": detected_type})
                if len(found) >= limit:
                    break

        return found[:limit]
