from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import tempfile
import os

from app.models.transcriber import Transcriber
from app.models.question_generator import QuestionGenerator
from app.models.evaluator import Evaluator
from app.models.sentiment_analyzer import SentimentAnalyzer

router = APIRouter()

# --- Lazy-loaded singletons (load once, reuse across requests) ---
_transcriber = None
_question_generator = None
_evaluator = None
_sentiment_analyzer = None


def get_transcriber():
    global _transcriber
    if _transcriber is None:
        _transcriber = Transcriber(model_size="base")
    return _transcriber


def get_question_generator():
    global _question_generator
    if _question_generator is None:
        _question_generator = QuestionGenerator(model="llama3.2:3b")
    return _question_generator


def get_evaluator():
    global _evaluator
    if _evaluator is None:
        _evaluator = Evaluator(model="llama3.2:3b")
    return _evaluator


def get_sentiment_analyzer():
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


# --- Request / Response schemas ---

class GenerateQuestionsRequest(BaseModel):
    job_description: str


class EvaluateRequest(BaseModel):
    question: str
    transcript: str


class SentimentRequest(BaseModel):
    transcript: str


# --- Routes ---

@router.post("/generate-questions")
async def generate_questions(body: GenerateQuestionsRequest):
    """
    Accepts a job description and returns 3 interview questions.
    """
    if not body.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description cannot be empty.")

    try:
        questions = get_question_generator().generate(body.job_description, num_questions=3)
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Accepts an audio file and returns the transcribed text.
    """
    allowed_types = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/ogg"}
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    # Save upload to a temp file for Whisper
    suffix = os.path.splitext(file.filename)[-1] if file.filename else ".wav"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        transcript = get_transcriber().transcribe(tmp_path)
        return {"transcript": transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/evaluate")
async def evaluate(body: EvaluateRequest):
    """
    Accepts a question and transcript, returns scored evaluation with rationale.
    """
    if not body.question.strip() or not body.transcript.strip():
        raise HTTPException(status_code=400, detail="question and transcript cannot be empty.")

    try:
        result = get_evaluator().evaluate(body.question, body.transcript)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/sentiment")
async def sentiment(body: SentimentRequest):
    """
    Accepts a transcript and returns sentiment label and confidence.
    """
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript cannot be empty.")

    try:
        result = get_sentiment_analyzer().analyze(body.transcript)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")
