// ------------------------------------------------------------------
// File: frontend/src/types.ts
// Purpose: Defines the shared data types used across the frontend.
// ------------------------------------------------------------------

// Data returned when the backend creates an interview question.
export interface Question {
    question: string;
    type: string;
}

// Score and written feedback for one evaluation category.
export interface DimensionScore {
    score: number;
    rationale: string;
}

// Rubric scores returned for one answer.
export interface EvaluationResult {
    relevance: DimensionScore;
    content_depth: DimensionScore;
    clarity_structure: DimensionScore;
    confidence_delivery: DimensionScore;
    overall_score: number | null;
}

// Sentiment label and confidence returned by the sentiment model.
export interface SentimentResult {
    label: string;
    confidence: number;
}

// All data collected for one submitted answer.
export interface SessionResult {
    question: string;
    question_type: string;
    transcript: string;
    evaluation: EvaluationResult;
    sentiment: SentimentResult;
    eye_contact_score: number | null;
}

// Overall report returned after an interview or loaded from history.
export interface ReportSummary {
    per_question: SessionResult[];
    avg_relevance: number;
    avg_content_depth: number;
    avg_clarity_structure: number;
    avg_confidence_delivery: number;
    avg_sentiment_score: number | null;
    avg_eye_contact: number | null;
    final_overall_score: number;
    dominant_sentiment: string;
    // These fields are set when a new report is saved.
    saved?: boolean;
    session_id?: number;
}

// Basic details for the logged-in user.
export interface User {
    id: number;
    email: string;
}

// Details shown for one saved session in the history list.
export interface SessionSummary {
    id: number;
    job_description: string;
    created_at: string;
    final_overall_score: number;
    dominant_sentiment: string;
    question_count: number;
}
