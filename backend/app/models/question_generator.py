import requests
import re


class QuestionGenerator:
    accepted_types = {"behavioural", "situational", "motivational", "technical"}

    def __init__(self, model="llama3.2:3b", host="http://localhost:11434"):
        self.llm_model = model
        self.endpoint = f"{host}/api/generate"

    def generate(self, jd_text, num_questions=3):
        prompt = (
            f"You are an expert interviewer. Based on the job description below, "
            f"generate exactly {num_questions} interview questions.\n\n"
            f"Each question must be one of these types: Behavioural, Situational, Motivational, Technical.\n\n"
            f"Rules:\n"
            f"- Use a mix of question types across the {num_questions} questions.\n"
            f"- Output ONLY in this exact format, nothing else:\n"
            f"  1. [Type] Question text\n"
            f"  2. [Type] Question text\n"
            f"  3. [Type] Question text\n"
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
        return self._extract_questions(raw, num_questions)

    def _extract_questions(self, raw, limit):
        found = []
        bracketed = re.compile(r"^\d+[\.\)]\s*\[(\w+)\]\s*(.+)$", re.IGNORECASE)
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
                if qtype.lower() not in self.accepted_types:
                    qtype = "General"
                found.append({"question": qtext, "type": qtype})
            if len(found) >= limit:
                break

        if not found:
            for row in raw.splitlines():
                row = row.strip()
                if row and row[0].isdigit():
                    for sep in [".", ")", ":"]:
                        if sep in row[:3]:
                            row = row.split(sep, 1)[-1].strip()
                            break
                    detected_type = "General"
                    for t in self.accepted_types:
                        if row.lower().startswith(t):
                            detected_type = t.capitalize()
                            row = row[len(t):].strip()
                            break
                    if row:
                        found.append({"question": row, "type": detected_type})
                if len(found) >= limit:
                    break

        return found[:limit]
