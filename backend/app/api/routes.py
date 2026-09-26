# ------------------------------------------------------------------
# File: backend/app/api/routes.py
# Purpose: Provides the main API endpoints for questions, answers, and reports.
# ------------------------------------------------------------------

# Import the libraries and modules needed for this API file
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import tempfile
import os
import requests as http_req

# Import the pipeline and database models used by the endpoints
from app.core.pipeline import InterviewPipeline
from app.models.question_generator import QuestionGenerator
from app.core.database import get_db
from app.core.db_models import User, InterviewSession, SessionAnswer
from app.api.auth import get_current_user_optional

# Create a router so these routes can be included in the FastAPI app
router = APIRouter()

# Keep one shared pipeline instance so we do not create a new one for every request
active_pipeline = None

def get_pipeline():
    """Return the shared InterviewPipeline object. Create it if it has not been made yet."""
    global active_pipeline
    if active_pipeline is None:
        active_pipeline = InterviewPipeline()
    return active_pipeline

def check_ollama():
    """Check whether the local Ollama service is running."""
    try:
        http_req.get("http://localhost:11434", timeout=3)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve",
        )

# ---------------------------
# Request body models
# ---------------------------
class JDInput(BaseModel):
    """Input for generating interview questions from a job description."""
    job_description: str
    num_questions: int = 3
    question_types: list[str] | None = None

class EvalInput(BaseModel):
    """Input for evaluating one answer from the candidate."""
    question: str
    transcript: str
    question_type: str = "General"

class ToneInput(BaseModel):
    """Input for sentiment analysis of a transcript."""
    transcript: str

class ReportInput(BaseModel):
    """Input for creating the final interview report."""
    results: list[dict]
    job_description: str | None = None

# ---------------------------
# API endpoints
# ---------------------------
# Generate interview questions from a job description
@router.post("/generate-questions")
async def generate_questions(body: JDInput):
    """Create interview questions based on the job description."""
    if not body.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description cannot be empty.")
    if not 1 <= body.num_questions <= 5:
        raise HTTPException(status_code=400, detail="num_questions must be between 1 and 5.")
    if body.question_types is not None:
        if not body.question_types:
            raise HTTPException(status_code=400, detail="question_types cannot be an empty list.")
        invalid = [t for t in body.question_types if t.lower() not in QuestionGenerator.accepted_types]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid question type(s): {', '.join(invalid)}")
    check_ollama()
    try:
        questions = get_pipeline().generate_questions(
            body.job_description, total=body.num_questions, types=body.question_types
        )
        return {"questions": questions}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(ex)}")

# Turn an uploaded audio file into text
@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Convert uploaded audio into a transcript string."""
    ok_types = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/ogg"}
    if file.content_type and file.content_type not in ok_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    # Whisper needs a file path, so save the upload to a temp file first
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
        # Always delete the temp file, even if transcription failed
        if saved_path and os.path.exists(saved_path):
            os.remove(saved_path)


# Score one candidate answer based on the question and transcript
@router.post("/evaluate")
async def evaluate_answer(body: EvalInput):
    """Evaluate one answer using the question and transcript."""
    if not body.question.strip() or not body.transcript.strip():
        raise HTTPException(status_code=400, detail="question and transcript cannot be empty.")
    check_ollama()
    try:
        result = get_pipeline().evaluate_answer(body.question, body.transcript, body.question_type)
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(ex)}")


# Detect the emotional tone of the answer text
@router.post("/sentiment")
async def get_sentiment(body: ToneInput):
    """Return the sentiment result for a transcript."""
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript cannot be empty.")
    try:
        result = get_pipeline().analyze_sentiment(body.transcript)
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(ex)}")


# Process one full answer from audio upload to scoring output
@router.post("/process-answer")
async def process_single_answer(question: str, question_type: str = "General", file: UploadFile = File(...)):
    """Process one answer end-to-end in one request."""
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


# Build the final report and save it to the database for logged-in users
@router.post("/final-report")
async def get_final_report(
    body: ReportInput,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Create the final report from all answer results."""
    if not body.results:
        raise HTTPException(status_code=400, detail="results cannot be empty.")
    try:
        summary = get_pipeline().aggregate_results(body.results)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(ex)}")

    # Only save the session if someone is logged in
    if current_user is not None:
        session = InterviewSession(
            user_id=current_user.id,
            job_description=body.job_description or "",
            final_overall_score=summary["final_overall_score"],
            avg_relevance=summary["avg_relevance"],
            avg_content_depth=summary["avg_content_depth"],
            avg_clarity_structure=summary["avg_clarity_structure"],
            avg_confidence_delivery=summary["avg_confidence_delivery"],
            avg_sentiment_score=summary.get("avg_sentiment_score"),
            avg_eye_contact=summary.get("avg_eye_contact"),
            dominant_sentiment=summary["dominant_sentiment"],
        )
        db.add(session)
        # Flush so the session gets an id before the answers are linked to it
        db.flush()

        for idx, item in enumerate(body.results):
            ev = item["evaluation"]
            se = item["sentiment"]
            db.add(SessionAnswer(
                session_id=session.id,
                order_index=idx,
                question=item["question"],
                question_type=item.get("question_type", "General"),
                transcript=item["transcript"],
                relevance_score=ev["relevance"]["score"],
                relevance_rationale=ev["relevance"]["rationale"],
                content_depth_score=ev["content_depth"]["score"],
                content_depth_rationale=ev["content_depth"]["rationale"],
                clarity_structure_score=ev["clarity_structure"]["score"],
                clarity_structure_rationale=ev["clarity_structure"]["rationale"],
                confidence_delivery_score=ev["confidence_delivery"]["score"],
                confidence_delivery_rationale=ev["confidence_delivery"]["rationale"],
                sentiment_label=se["label"],
                sentiment_confidence=se["confidence"],
                eye_contact_score=item.get("eye_contact_score"),
            ))
        db.commit()
        summary["session_id"] = session.id
        summary["saved"] = True
    else:
        summary["saved"] = False

    return summary
