# Import necessary libraries
import requests
import re

class QuestionGenerator:
    """
    Generates interview questions from a job description using an Ollama model.
    The generated questions are expected to include a question type
    (Behavioural, Situational, Motivational, or Technical), and the
    output is parsed into a structured list for the rest of the system.
    """
    accepted_types = {"behavioural", "situational", "motivational", "technical"}

    def __init__(self, model="llama3.2:3b", host="http://localhost:11434"):
        """
        Initialise the question generator with the selected model and Ollama host.
        """
        self.llm_model = model
        self.endpoint = f"{host}/api/generate"

    def generate(self, jd_text, num_questions=3, allowed_types=None):
        """
        Generate interview questions from a job description.
        The model is prompted to return exactly the requested number of questions,
        each labelled with one of the accepted question types.
        Parameters:
        - allowed_types: optional list of type names to restrict generation to
                          (e.g. ["Behavioural", "Technical"]). Defaults to all
                          four accepted types.
        Returns:
            list[dict]: A list of question objects in the form:
                        {"question": "...", "type": "..."}
        """
        types_to_use = allowed_types if allowed_types else ["Behavioural", "Situational", "Motivational", "Technical"]
        accepted_this_call = {t.lower() for t in types_to_use}
        types_str = ", ".join(types_to_use)

        mix_rule = (
            f"- Use a mix of question types across the {num_questions} questions.\n"
            if len(types_to_use) > 1
            else f"- Every question must be of type {types_to_use[0]}.\n"
        )
        example_lines = "".join(f"  {i}. [Type] Question text\n" for i in range(1, num_questions + 1))

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

        res = requests.post(self.endpoint, json=body, timeout=60)
        res.raise_for_status()

        raw = res.json().get("response", "").strip()
        return self._extract_questions(raw, num_questions, accepted_this_call)

    def _extract_questions(self, raw, limit, accepted_types=None):
        """
        Parse the raw model output into structured question objects.
        The function first tries to match the expected format:
            1. [Type] Question text
        If that fails, it falls back to a looser extraction approach so that
        minor formatting issues from the model do not break the system.
        Returns:
            list[dict]: Parsed list of question dictionaries.
        """
        accepted = accepted_types if accepted_types else self.accepted_types
        found = []

        # Matches format like: 1. [Technical] What is...?
        bracketed = re.compile(r"^\d+[\.\)]\s*\[(\w+)\]\s*(.+)$", re.IGNORECASE)
        
        # Matches format like: 1. Technical What is...?
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
                
                # If the detected type is not one of the accepted ones, use General as a fallback.
                if qtype.lower() not in accepted:
                    qtype = "General"
                found.append({"question": qtext, "type": qtype})
            if len(found) >= limit:
                break

        # Fallback parsing in case the model did not fully follow the format
        if not found:
            for row in raw.splitlines():
                row = row.strip()
                if row and row[0].isdigit():
                    for sep in [".", ")", ":"]:

                        # Remove numbering such as "1.", "2)", or "3:"
                        if sep in row[:3]:
                            row = row.split(sep, 1)[-1].strip()
                            break
                    detected_type = "General"
                    
                    # Try to detect the question type from the start of the line
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
