from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import tempfile
import os
import requests as http_req

from app.core.pipeline import InterviewPipeline

router = APIRouter()

active_pipeline = None


def get_pipeline():
    global active_pipeline
    if active_pipeline is None:
        active_pipeline = InterviewPipeline()
    return active_pipeline


def check_ollama():
    try:
        http_req.get("http://localhost:11434", timeout=3)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve",
        )


class JDInput(BaseModel):
    job_description: str


class EvalInput(BaseModel):
    question: str
    transcript: str
    question_type: str = "General"


class ToneInput(BaseModel):
    transcript: str


class ReportInput(BaseModel):
    results: list[dict]


@router.post("/generate-questions")
async def generate_questions(body: JDInput):
    if not body.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description cannot be empty.")
    check_ollama()
    try:
        questions = get_pipeline().generate_questions(body.job_description)
        return {"questions": questions}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(ex)}")


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    ok_types = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/ogg"}
    if file.content_type and file.content_type not in ok_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    ext = os.path.splitext(file.filename)[-1] if file.filename else ".wav"
    saved_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            saved_path = tmp.name

        transcript = get_pipeline().transcribe(saved_path)
        return {"transcript": transcript}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(ex)}")
    finally:
        if saved_path and os.path.exists(saved_path):
            os.remove(saved_path)


@router.post("/evaluate")
async def evaluate_answer(body: EvalInput):
    if not body.question.strip() or not body.transcript.strip():
        raise HTTPException(status_code=400, detail="question and transcript cannot be empty.")
    check_ollama()
    try:
        result = get_pipeline().evaluate_answer(body.question, body.transcript, body.question_type)
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(ex)}")


@router.post("/sentiment")
async def get_sentiment(body: ToneInput):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript cannot be empty.")
    try:
        result = get_pipeline().analyze_sentiment(body.transcript)
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(ex)}")


@router.post("/process-answer")
async def process_single_answer(question: str, question_type: str = "General", file: UploadFile = File(...)):
    if not question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty.")

    ok_types = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/ogg"}
    if file.content_type and file.content_type not in ok_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    check_ollama()
    ext = os.path.splitext(file.filename)[-1] if file.filename else ".wav"
    saved_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            saved_path = tmp.name

        result = get_pipeline().process_answer(question, saved_path, question_type)
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(ex)}")
    finally:
        if saved_path and os.path.exists(saved_path):
            os.remove(saved_path)


@router.post("/final-report")
async def get_final_report(body: ReportInput):
    if not body.results:
        raise HTTPException(status_code=400, detail="results cannot be empty.")
    try:
        summary = get_pipeline().aggregate_results(body.results)
        return summary
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(ex)}")
