import type { ReportSummary } from "../types";

const TONE_LABELS: Record<string, string> = {
  POSITIVE: "Positive tone",
  NEUTRAL: "Neutral tone",
  NEGATIVE: "Negative tone",
};

function toneLabel(raw: string): string {
  return TONE_LABELS[raw] ?? raw;
}

function sentimentToScore(label: string, confidence: number): number {
  const base: Record<string, number> = { POSITIVE: 10, NEUTRAL: 5, NEGATIVE: 0 };
  return Math.round((base[label] ?? 5) * confidence * 10) / 10;
}

function fmtEye(val: number | null | undefined): string {
  return val === null || val === undefined ? "N/A" : `${val}/10`;
}

type DimensionKey = "relevance" | "content_depth" | "clarity_structure" | "confidence_delivery";

const DIMENSIONS: { key: DimensionKey; label: string }[] = [
  { key: "relevance", label: "Relevance" },
  { key: "content_depth", label: "Content Depth" },
  { key: "clarity_structure", label: "Clarity & Structure" },
  { key: "confidence_delivery", label: "Confidence Delivery" },
];

interface ReportScreenProps {
  summary: ReportSummary;
  onRestart: () => void;
}

export function ReportScreen({ summary, onRestart }: ReportScreenProps) {
  return (
    <div className="screen">
      <h1>Final Report</h1>

      <div className="summary-box">
        <h2>Overall Results</h2>
        <div className="score-row">
          <span>
            Relevance <span className="weight-tag">20%</span>
          </span>
          <span className="val">{summary.avg_relevance}/10</span>
        </div>
        <div className="score-row">
          <span>
            Content Depth <span className="weight-tag">20%</span>
          </span>
          <span className="val">{summary.avg_content_depth}/10</span>
        </div>
        <div className="score-row">
          <span>
            Clarity &amp; Structure <span className="weight-tag">20%</span>
          </span>
          <span className="val">{summary.avg_clarity_structure}/10</span>
        </div>
        <div className="score-row">
          <span>
            Confidence Delivery <span className="weight-tag">20%</span>
          </span>
          <span className="val">{summary.avg_confidence_delivery}/10</span>
        </div>
        <div className="score-row">
          <span>
            Sentiment <span className="weight-tag">10%</span>
          </span>
          <span className="val">
            {summary.avg_sentiment_score !== null && summary.avg_sentiment_score !== undefined
              ? `${summary.avg_sentiment_score}/10`
              : "N/A"}
          </span>
        </div>
        <div className="score-row">
          <span>
            Eye Contact <span className="weight-tag">10%</span>
          </span>
          <span className="val">{fmtEye(summary.avg_eye_contact)}</span>
        </div>
        <div className="score-row final-score">
          <span>Final Weighted Score</span>
          <span className="val">{summary.final_overall_score}/10</span>
        </div>
        <div className="score-row">
          <span>Answer Tone</span>
          <span className={`sentiment-tag ${summary.dominant_sentiment}`}>
            {toneLabel(summary.dominant_sentiment)}
          </span>
        </div>
      </div>

      <div id="report-questions">
        {summary.per_question.map((item, idx) => (
          <div className="question-result" key={idx}>
            <h3>
              Q{idx + 1}: {item.question}
              {item.question_type !== "General" && <span className="type-tag"> ({item.question_type})</span>}
            </h3>
            <p className="transcript-preview">"{item.transcript}"</p>

            {DIMENSIONS.map((d) => (
              <div className="dim-row" key={d.key}>
                <div className="dim-header">
                  <span>{d.label}</span>
                  <span>{item.evaluation[d.key].score}/10</span>
                </div>
                <div className="rationale">{item.evaluation[d.key].rationale}</div>
              </div>
            ))}

            <div className="result-footer">
              <div className="tone-row">
                <span className={`sentiment-tag ${item.sentiment.label}`}>{toneLabel(item.sentiment.label)}</span>
                <strong className="overall-score">Overall: {item.evaluation.overall_score}/10</strong>
              </div>
              <div className="sentiment-score-row">
                <span className="eye-score-tag">
                  Sentiment: {sentimentToScore(item.sentiment.label, item.sentiment.confidence)}/10
                </span>
              </div>
              <div className="eye-contact-row">
                <span className="eye-score-tag">👁 Eye Contact: {fmtEye(item.eye_contact_score)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <button onClick={onRestart}>Start Over</button>
    </div>
  );
}
