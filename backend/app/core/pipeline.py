# Import the individual model wrapper classes
from app.models.question_generator import QuestionGenerator
from app.models.transcriber import Transcriber
from app.models.evaluator import Evaluator
from app.models.sentiment_analyzer import SentimentAnalyzer

# Weight configuration used when calculating the final overall score.
WEIGHTS = {
    "relevance":           0.20,
    "content_depth":       0.20,
    "clarity_structure":   0.20,
    "confidence_delivery": 0.20,
    "sentiment":           0.10,
    "eye_contact":         0.10,
}

# Converts sentiment labels into a base score out of 10.
SENTIMENT_BASE = {
    "POSITIVE": 10,
    "NEUTRAL":  5,
    "NEGATIVE": 0,
}

def sentiment_to_score(label, confidence):
    """
    Convert the sentiment label and confidence into a numeric score.
    Example:
    - POSITIVE with confidence 0.80 -> 10 * 0.80 = 8.0
    - NEUTRAL with confidence 0.60 -> 5 * 0.60 = 3.0
    """
    base = SENTIMENT_BASE.get(label.upper(), 5)
    return round(base * confidence, 2)

class InterviewPipeline:
    """
    Main orchestration class for the interview system.
    This class combines all model wrappers into a single reusable pipeline.
    It handles:
    - question generation
    - transcription
    - answer evaluation
    - sentiment analysis
    - final score aggregation
    """
    def __init__(self, ollama_model="llama3.2:3b", whisper_size="small", ollama_host="http://localhost:11434"):
        """
        Initialise all model components used by the system.
        Parameters:
        - ollama_model: model used for question generation and evaluation
        - whisper_size: Whisper model size used for transcription
        - ollama_host: local Ollama server address
        """
        self.question_gen = QuestionGenerator(model=ollama_model, host=ollama_host)
        self.speech_to_text = Transcriber(model_size=whisper_size)
        self.answer_evaluator = Evaluator(model=ollama_model, host=ollama_host)
        self.tone_analyzer = SentimentAnalyzer()


    def generate_questions(self, jd_text, total=3, types=None):
        """
        Generate interview questions from a job description.
        Parameters:
        - jd_text: job description text
        - total: number of questions to generate
        - types: optional list of question types to restrict generation to
        Returns:
        - list of generated questions
        """
        return self.question_gen.generate(jd_text, num_questions=total, allowed_types=types)

    def transcribe(self, audio_file):
        """
        Convert an audio file into text using Whisper.
        Parameters:
        - audio_file: path to the audio file
        Returns:
        - transcript string
        """
        return self.speech_to_text.transcribe(audio_file)

    def evaluate_answer(self, question, transcript, qtype="General"):
        """
        Evaluate a candidate's answer using the evaluator model.
        Parameters:
        - question: the interview question asked
        - transcript: transcribed candidate answer
        - qtype: question type/category
        Returns:
        - dictionary containing evaluation scores for each dimension
        """
        return self.answer_evaluator.evaluate(question, transcript, qtype)

    def analyze_sentiment(self, transcript):
        """
        Analyze the sentiment of a transcript.
        Parameters:
        - transcript: candidate's transcribed answer
        Returns:
        - sentiment result with label and confidence
        """
        return self.tone_analyzer.analyze(transcript)

    def process_answer(self, question, audio_file, qtype="General"):
        """
        Process one interview answer end-to-end.
        Steps:
        1. Transcribe the audio
        2. Evaluate the transcribed answer
        3. Analyze the transcript sentiment
        4. Return all results together
        Parameters:
        - question: interview question
        - audio_file: path to uploaded audio file
        - qtype: question category
        Returns:
        - dictionary containing question, transcript, evaluation, and sentiment
        """
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
        """
        Aggregate results from all interview questions into a final report.
        This method:
        - averages the LLM evaluation scores
        - converts sentiment into numeric scores and averages them
        - averages eye contact scores
        - computes a final weighted score
        - identifies the dominantsentiment across the session
        Parameters:
        - session_results: list of per-question result dictionaries
        Returns:
        - summary dictionary containing averages and final score
        """
        if not session_results:
            return {}

        score_keys = ["relevance", "content_depth", "clarity_structure", "confidence_delivery"]
        running_totals = {k: 0 for k in score_keys}
        running_sentiment_score = 0
        running_weighted = 0
        running_eye_score = 0
        tone_list = []
        eye_count = 0

        # Process each answer result one by one
        for entry in session_results:
            ev = entry["evaluation"]
            se = entry["sentiment"]
            eye = entry.get("eye_contact_score")

            for k in score_keys:
                running_totals[k] += ev[k]["score"]

            s_score = sentiment_to_score(se["label"], se["confidence"])
            running_sentiment_score += s_score
            tone_list.append(se["label"])

            if eye is not None:
                running_eye_score += eye
                eye_count += 1

            eye_weight_used = WEIGHTS["eye_contact"] if eye is not None else 0
            eye_val = eye if eye is not None else 0
            llm_weight_total = (
                WEIGHTS["relevance"] + WEIGHTS["content_depth"] +
                WEIGHTS["clarity_structure"] + WEIGHTS["confidence_delivery"]
            )
            remaining_weight = 1.0 - WEIGHTS["sentiment"] - eye_weight_used
            scale = remaining_weight / llm_weight_total if llm_weight_total > 0 else 1

            weighted = (
                ev["relevance"]["score"]           * WEIGHTS["relevance"]           * scale +
                ev["content_depth"]["score"]        * WEIGHTS["content_depth"]        * scale +
                ev["clarity_structure"]["score"]    * WEIGHTS["clarity_structure"]    * scale +
                ev["confidence_delivery"]["score"]  * WEIGHTS["confidence_delivery"]  * scale +
                s_score                             * WEIGHTS["sentiment"] +
                eye_val                             * eye_weight_used
            )
            running_weighted += weighted


        # Number of questions answered in the session
        n = len(session_results)

        # Average LLM dimension scores
        avg_scores = {k: round(running_totals[k] / n, 1) for k in score_keys}

        # Average sentiment score
        avg_sentiment_score = round(running_sentiment_score / n, 1)

        # Average eye contact score
        avg_eye = round(running_eye_score / eye_count, 1) if eye_count > 0 else None

        # Most common sentiment label across all answers
        top_tone = max(set(tone_list), key=tone_list.count)


        # Return final summary report
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
