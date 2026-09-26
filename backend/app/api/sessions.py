# ------------------------------------------------------------------
# File: backend/app/api/sessions.py
# Purpose: Provides API endpoints for listing and viewing saved interview sessions.
# ------------------------------------------------------------------

# Import the libraries and modules needed for the session routes
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.db_models import InterviewSession, User
from app.api.auth import get_current_user

# Create a router for the session endpoints
router = APIRouter()

# Show a quick summary of all past sessions for the currently logged-in user
@router.get("/sessions")
def list_sessions(current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    """Return a simple list of previous sessions, newest first."""
    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == current_user.id)
        .order_by(InterviewSession.created_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "job_description": s.job_description,
            "created_at": s.created_at.isoformat(),
            "final_overall_score": s.final_overall_score,
            "dominant_sentiment": s.dominant_sentiment,
            "question_count": len(s.answers),
        }
        for s in sessions
    ]


# Return one full saved interview session, in a format that the frontend can display
@router.get("/sessions/{session_id}")
def get_session(session_id: int, current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    """Return the details of one saved session."""
    session = (
        db.query(InterviewSession)
        .filter(InterviewSession.id == session_id, InterviewSession.user_id == current_user.id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    per_question = [
        {
            "question": a.question,
            "question_type": a.question_type,
            "transcript": a.transcript,
            "evaluation": {
                "relevance": {"score": a.relevance_score, "rationale": a.relevance_rationale},
                "content_depth": {"score": a.content_depth_score, "rationale": a.content_depth_rationale},
                "clarity_structure": {"score": a.clarity_structure_score, "rationale": a.clarity_structure_rationale},
                "confidence_delivery": {
                    "score": a.confidence_delivery_score,
                    "rationale": a.confidence_delivery_rationale,
                },
                "overall_score": round(
                    (
                        a.relevance_score
                        + a.content_depth_score
                        + a.clarity_structure_score
                        + a.confidence_delivery_score
                    )
                    / 4,
                    1,
                ),
            },
            "sentiment": {"label": a.sentiment_label, "confidence": a.sentiment_confidence},
            "eye_contact_score": a.eye_contact_score,
        }
        for a in session.answers
    ]

    return {
        "id": session.id,
        "job_description": session.job_description,
        "created_at": session.created_at.isoformat(),
        "per_question": per_question,
        "avg_relevance": session.avg_relevance,
        "avg_content_depth": session.avg_content_depth,
        "avg_clarity_structure": session.avg_clarity_structure,
        "avg_confidence_delivery": session.avg_confidence_delivery,
        "avg_sentiment_score": session.avg_sentiment_score,
        "avg_eye_contact": session.avg_eye_contact,
        "final_overall_score": session.final_overall_score,
        "dominant_sentiment": session.dominant_sentiment,
    }
