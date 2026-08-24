# Import necessary libraries
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import tempfile
import os
import requests as http_req

# Import the main pipeline class that handles interview processing logic
from app.core.pipeline import InterviewPipeline
from app.models.question_generator import QuestionGenerator

# Create a router object so all endpoints in this file can be included in the app
router = APIRouter()

# Global pipeline instance (Only one instance of the pipeline is created and reused for all requests to save resources)
active_pipeline = None

def get_pipeline():
    """
    Returns the shared InterviewPipeline instance.
    If it doesn't exist yet, create it first.
    This avoids creating a new pipeline object for every request.
    """
    global active_pipeline
    if active_pipeline is None:
        active_pipeline = InterviewPipeline()
    return active_pipeline

def check_ollama():
    """
    Checks whether the Ollama service is running on localhost:11434.
    If not reachable, return a 503 Service Unavailable error.
    """
    try:
        http_req.get("http://localhost:11434", timeout=3)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve",
        )

# ---------------------------
# Request body schemas
# ---------------------------
class JDInput(BaseModel):
    """
    Request model for generating interview questions.
    Expects a job description string, and optionally how many questions to
    generate and which question types to restrict generation to.
    """
    job_description: str
    num_questions: int = 3
    question_types: list[str] | None = None

class EvalInput(BaseModel):
    """
    Request model for evaluating an answer.
    Includes:
    - question: the interview question asked
    - transcript: the candidate's transcribed answer
    - question_type: category of question (default = General)
    """
    question: str
    transcript: str
    question_type: str = "General"

class ToneInput(BaseModel):
    """
    Request model for sentiment analysis.
    Expects only the transcript text.
    """
    transcript: str

class ReportInput(BaseModel):
    """
    Request model for generating the final report.
    Expects a list of results from previous questions.
    """
    results: list[dict]

# ---------------------------
# API Endpoints
# ---------------------------
@router.post("/generate-questions")
async def generate_questions(body: JDInput):
    """
    Generate interview questions based on a job description.
    Steps:
    1. Validate that the job description is not empty
    2. Check that Ollama is available
    3. Use the pipeline to generate questions
    4. Return the generated questions
    """
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

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe an uploaded audio file into text.
    Steps:
    1. Check whether the uploaded file type is supported
    2. Save the uploaded file temporarily
    3. Pass the file path to the pipeline for transcription
    4. Return the transcript
    5. Delete the temp file once done
    """
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
    """
    Evaluate a candidate's answer using the transcript.
    Steps:
    1. Validate that question and transcript are not empty
    2. Check that Ollama is running
    3. Call the pipeline to evaluate the answer
    4. Return evaluation results
    """
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
    """
    Analyze the sentiment of a transcript.
    Steps:
    1. Validate that transcript is not empty
    2. Pass transcript to the pipeline's sentiment analyzer
    3. Return sentiment result
    """
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="transcript cannot be empty.")
    try:
        result = get_pipeline().analyze_sentiment(body.transcript)
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(ex)}")


@router.post("/process-answer")
async def process_single_answer(question: str, question_type: str = "General", file: UploadFile = File(...)):
    """
    Process one interview answer end-to-end in a single API call.
    Steps:
    1. Validate question is not empty
    2. Validate uploaded file type
    3. Check Ollama availability
    4. Save uploaded file temporarily
    5. Pass question + file path + question type to pipeline
    6. Return the full processed result
    7. Delete temp file once done
    """
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
    """
    Generate the final interview report from all question results.
    Steps:
    1. Validate that results list is not empty
    2. Aggregate all results using the pipeline
    3. Return the final summary/report
    """
    if not body.results:
        raise HTTPException(status_code=400, detail="results cannot be empty.")
    try:
        summary = get_pipeline().aggregate_results(body.results)
        return summary
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(ex)}")
