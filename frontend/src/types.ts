export interface Question {
  question: string;
  type: string;
}

export interface DimensionScore {
  score: number;
  rationale: string;
}

export interface EvaluationResult {
  relevance: DimensionScore;
  content_depth: DimensionScore;
  clarity_structure: DimensionScore;
  confidence_delivery: DimensionScore;
  overall_score: number | null;
}

export interface SentimentResult {
  label: string;
  confidence: number;
}

export interface SessionResult {
  question: string;
  question_type: string;
  transcript: string;
  evaluation: EvaluationResult;
  sentiment: SentimentResult;
  eye_contact_score: number | null;
}

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
}
