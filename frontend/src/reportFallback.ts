import type { SessionResult, ReportSummary } from "./types";

function sentimentToScore(label: string, confidence: number): number {
  const base: Record<string, number> = { POSITIVE: 10, NEUTRAL: 5, NEGATIVE: 0 };
  return Math.round((base[label] ?? 5) * confidence * 10) / 10;
}

/**
 * The same weighted formula the backend uses in aggregate_results(), applied to a
 * single answer. Used so a per-question ring shows the same "overall score" concept
 * as the session summary (sentiment + eye contact included), not the LLM's own
 * unweighted overall_score field (which only averages the 4 rubric dimensions).
 */
export function computeWeightedScore(r: SessionResult): number {
  const sScore = sentimentToScore(r.sentiment.label, r.sentiment.confidence);
  const eyeVal = r.eye_contact_score ?? null;
  const eyeWeightUsed = eyeVal !== null ? 0.1 : 0;
  const llmScale = (1.0 - 0.1 - eyeWeightUsed) / 0.8;
  return (
    r.evaluation.relevance.score * 0.2 * llmScale +
    r.evaluation.content_depth.score * 0.2 * llmScale +
    r.evaluation.clarity_structure.score * 0.2 * llmScale +
    r.evaluation.confidence_delivery.score * 0.2 * llmScale +
    sScore * 0.1 +
    (eyeVal ?? 0) * eyeWeightUsed
  );
}

function avgSentiment(data: SessionResult[]): number | null {
  const scores = data.map((r) => sentimentToScore(r.sentiment.label, r.sentiment.confidence));
  if (!scores.length) return null;
  return Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10;
}

function avgGaze(data: SessionResult[]): number | null {
  const valid = data.map((r) => r.eye_contact_score).filter((s): s is number => s !== null && s !== undefined);
  if (!valid.length) return null;
  return Math.round((valid.reduce((a, b) => a + b, 0) / valid.length) * 10) / 10;
}

/** Client-side fallback used only if the backend's /final-report call fails. */
export function fallbackAggregate(data: SessionResult[]): ReportSummary {
  const keys = ["relevance", "content_depth", "clarity_structure", "confidence_delivery"] as const;
  const sums: Record<(typeof keys)[number], number> = {
    relevance: 0,
    content_depth: 0,
    clarity_structure: 0,
    confidence_delivery: 0,
  };
  let weightedTotal = 0;
  const tones: string[] = [];

  data.forEach((r) => {
    keys.forEach((k) => {
      sums[k] += r.evaluation[k].score;
    });
    weightedTotal += computeWeightedScore(r);
    tones.push(r.sentiment.label);
  });

  const n = data.length;
  const dominant = tones.sort(
    (a, b) => tones.filter((v) => v === b).length - tones.filter((v) => v === a).length
  )[0];

  return {
    per_question: data,
    avg_relevance: +(sums.relevance / n).toFixed(1),
    avg_content_depth: +(sums.content_depth / n).toFixed(1),
    avg_clarity_structure: +(sums.clarity_structure / n).toFixed(1),
    avg_confidence_delivery: +(sums.confidence_delivery / n).toFixed(1),
    avg_sentiment_score: avgSentiment(data),
    avg_eye_contact: avgGaze(data),
    final_overall_score: +(weightedTotal / n).toFixed(1),
    dominant_sentiment: dominant,
  };
}
