# ------------------------------------------------------------------
# File: backend/app/core/db_models.py
# Purpose: Defines the database tables for users, interviews, and saved answers.
# ------------------------------------------------------------------

# Import the libraries needed for the database models
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

# Return the current UTC time for created_at fields
def utcnow():
    return datetime.now(timezone.utc)

# User table for login and account information
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")

# One saved interview session for one user
class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    final_overall_score = Column(Float, nullable=False)
    avg_relevance = Column(Float, nullable=False)
    avg_content_depth = Column(Float, nullable=False)
    avg_clarity_structure = Column(Float, nullable=False)
    avg_confidence_delivery = Column(Float, nullable=False)
    avg_sentiment_score = Column(Float, nullable=False)
    avg_eye_contact = Column(Float, nullable=True)
    dominant_sentiment = Column(String, nullable=False)

    user = relationship("User", back_populates="sessions")
    answers = relationship(
        "SessionAnswer",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionAnswer.order_index",
    )

# One answer saved inside an interview session
class SessionAnswer(Base):
    __tablename__ = "session_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)

    question = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)
    transcript = Column(Text, nullable=False)

    relevance_score = Column(Float, nullable=False)
    relevance_rationale = Column(Text, nullable=False)
    content_depth_score = Column(Float, nullable=False)
    content_depth_rationale = Column(Text, nullable=False)
    clarity_structure_score = Column(Float, nullable=False)
    clarity_structure_rationale = Column(Text, nullable=False)
    confidence_delivery_score = Column(Float, nullable=False)
    confidence_delivery_rationale = Column(Text, nullable=False)

    sentiment_label = Column(String, nullable=False)
    sentiment_confidence = Column(Float, nullable=False)
    eye_contact_score = Column(Float, nullable=True)

    session = relationship("InterviewSession", back_populates="answers")
