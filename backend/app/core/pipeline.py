# ------------------------------------------------------------------
# File: backend/app/core/pipeline.py
# Purpose: Coordinates question generation, answer processing, and report scoring.
# ------------------------------------------------------------------

# Import the model classes used by the interview pipeline
from app.models.question_generator import QuestionGenerator
from app.models.transcriber import Transcriber
from app.models.evaluator import Evaluator
from app.models.sentiment_analyzer import SentimentAnalyzer

# Weight values used to calculate the final overall score
WEIGHTS = {
    "relevance":           0.20,
    "content_depth":       0.20,
    "clarity_structure":   0.20,
    "confidence_delivery": 0.20,
    "sentiment":           0.10,
    "eye_contact":         0.10,
}

# Base score for each sentiment label out of 10
SENTIMENT_BASE = {
    "POSITIVE": 10,
    "NEUTRAL":  5,
    "NEGATIVE": 0,
}

def sentiment_to_score(label, confidence):
    """Turn a sentiment label and confidence into a number score."""
    # Scale the base score by how confident the model was, unknown labels count as neutral
    base = SENTIMENT_BASE.get(label.upper(), 5)
    return round(base * confidence, 2)

class InterviewPipeline:
    """Run the interview workflow by combining all the model classes."""

    def __init__(self, ollama_model="llama3.2:3b", whisper_size="small", ollama_host="http://localhost:11434"):
        """Create the model objects used for each part of the interview flow."""
        self.question_gen = QuestionGenerator(model=ollama_model, host=ollama_host)
        self.speech_to_text = Transcriber(model_size=whisper_size)
        self.answer_evaluator = Evaluator(model=ollama_model, host=ollama_host)
        self.tone_analyzer = SentimentAnalyzer()

    def generate_questions(self, jd_text, total=3, types=None):
        """Create interview questions from the job description text."""
        return self.question_gen.generate(jd_text, num_questions=total, allowed_types=types)

    def transcribe(self, audio_file):
        """Convert an audio file to text using Whisper."""
        return self.speech_to_text.transcribe(audio_file)

    def evaluate_answer(self, question, transcript, qtype="General"):
        """Score a candidate answer using the evaluator model."""
        return self.answer_evaluator.evaluate(question, transcript, qtype)

    def analyze_sentiment(self, transcript):
        """Work out the sentiment of a transcript."""
        return self.tone_analyzer.analyze(transcript)

    def process_answer(self, question, audio_file, qtype="General"):
        """Transcribe, score, and analyse one answer in one call."""
        transcript = self.transcribe(audio_file)
        scores = self.evaluate_answer(question, transcript, qtype)
        tone = self.analyze_sentiment(transcript)

        return {
            "question":      question,
            "question_type": qtype,
            "transcript":    transcript,
            "evaluation":    scores,
            "sentiment":     tone,
        }

    def aggregate_results(self, session_results):
        """Combine all question results into the final session summary."""
        if not session_results:
            return {}

        # Running totals used to work out the averages at the end
        score_keys = ["relevance", "content_depth", "clarity_structure", "confidence_delivery"]
        running_totals = {k: 0 for k in score_keys}
        running_sentiment_score = 0
        running_weighted = 0
        running_eye_score = 0
        tone_list = []
        eye_count = 0

        # Go through each answer in the session and add its score to the totals
        for entry in session_results:
            ev = entry["evaluation"]
            se = entry["sentiment"]
            eye = entry.get("eye_contact_score")

            for k in score_keys:
                running_totals[k] += ev[k]["score"]

            s_score = sentiment_to_score(se["label"], se["confidence"])
            running_sentiment_score += s_score
            tone_list.append(se["label"])

            # Only count eye contact if the webcam tracked this answer
            if eye is not None:
                running_eye_score += eye
                eye_count += 1

            # If there is no eye contact score, its 10% weight is shared across
            # the four LLM scores so the weights still add up to 1.0
            eye_weight_used = WEIGHTS["eye_contact"] if eye is not None else 0
            eye_val = eye if eye is not None else 0
            llm_weight_total = (
                WEIGHTS["relevance"] + WEIGHTS["content_depth"] +
                WEIGHTS["clarity_structure"] + WEIGHTS["confidence_delivery"]
            )
            remaining_weight = 1.0 - WEIGHTS["sentiment"] - eye_weight_used
            scale = remaining_weight / llm_weight_total if llm_weight_total > 0 else 1

            # Weighted score for this answer out of 10
            weighted = (
                ev["relevance"]["score"]           * WEIGHTS["relevance"]           * scale +
                ev["content_depth"]["score"]        * WEIGHTS["content_depth"]        * scale +
                ev["clarity_structure"]["score"]    * WEIGHTS["clarity_structure"]    * scale +
                ev["confidence_delivery"]["score"]  * WEIGHTS["confidence_delivery"]  * scale +
                s_score                             * WEIGHTS["sentiment"] +
                eye_val                             * eye_weight_used
            )
            running_weighted += weighted

        # Work out the average score for the whole session
        n = len(session_results)
        avg_scores = {k: round(running_totals[k] / n, 1) for k in score_keys}
        avg_sentiment_score = round(running_sentiment_score / n, 1)
        avg_eye = round(running_eye_score / eye_count, 1) if eye_count > 0 else None
        # The most common sentiment label across all answers
        top_tone = max(set(tone_list), key=tone_list.count)

        return {
            "per_question":            session_results,
            "avg_relevance":           avg_scores["relevance"],
            "avg_content_depth":       avg_scores["content_depth"],
            "avg_clarity_structure":   avg_scores["clarity_structure"],
            "avg_confidence_delivery": avg_scores["confidence_delivery"],
            "avg_sentiment_score":     avg_sentiment_score,
            "avg_eye_contact":         avg_eye,
            "final_overall_score":     round(running_weighted / n, 1),
            "dominant_sentiment":      top_tone,
        }
