import requests
import json


class QuestionGenerator:
    """
    Uses a local Ollama model to generate interview questions from a job description.
    """

    def __init__(self, model: str = "llama3.2:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.api_url = f"{host}/api/generate"

    def generate(self, job_description: str, num_questions: int = 3) -> list[str]:
        """
        Generates interview questions based on a job description.

        Args:
            job_description: The job description text.
            num_questions: How many questions to generate.

        Returns:
            A list of question strings.
        """
        prompt = (
            f"You are an expert interviewer. Based on the following job description, "
            f"generate exactly {num_questions} interview questions.\n\n"
            f"Rules:\n"
            f"- Output ONLY the questions, numbered 1 to {num_questions}.\n"
            f"- No explanations, no headers, no extra text.\n"
            f"- Each question on its own line.\n\n"
            f"Job Description:\n{job_description}\n\n"
            f"Questions:"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        response = requests.post(self.api_url, json=payload, timeout=60)
        response.raise_for_status()

        raw_text = response.json().get("response", "").strip()
        return self._parse_questions(raw_text, num_questions)

    def _parse_questions(self, raw_text: str, num_questions: int) -> list[str]:
        """
        Parses numbered questions from the model's raw output.
        """
        lines = raw_text.splitlines()
        questions = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Strip leading number and punctuation e.g. "1." "1)" "1:"
            if line[0].isdigit():
                # Remove the numbering prefix
                for sep in [".", ")", ":"]:
                    if sep in line[:3]:
                        line = line.split(sep, 1)[-1].strip()
                        break
            if line:
                questions.append(line)

        # Fallback: if parsing produces nothing, return raw lines
        if not questions:
            questions = [l.strip() for l in lines if l.strip()]

        return questions[:num_questions]
