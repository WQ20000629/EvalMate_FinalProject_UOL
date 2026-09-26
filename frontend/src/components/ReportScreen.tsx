// ------------------------------------------------------------------
// File: frontend/src/components/ReportScreen.tsx
// Purpose: Displays the final interview scores and written feedback.
// ------------------------------------------------------------------

// Types and components used to display the final report.
import type { ReportSummary, SessionResult } from "../types";
import { ScoreRing } from "./ScoreRing";
import { MetricMeter } from "./MetricMeter";
import { computeWeightedScore } from "../reportFallback";

// Display text for each sentiment label from the backend.
const TONE_LABELS: Record<string, string> = {
    POSITIVE: "Positive tone",
    NEUTRAL: "Neutral tone",
    NEGATIVE: "Negative tone",
};

// Convert the backend tone label into text for the interface.
function toneLabel(raw: string): string {
    return TONE_LABELS[raw] ?? raw;
}

// Keys of the four rubric scores in an evaluation result.
type DimensionKey =
    "relevance" | "content_depth" | "clarity_structure" | "confidence_delivery";

// Rubric scores shown on each question card, in display order.
const DIMENSIONS: { key: DimensionKey; label: string }[] = [
    { key: "relevance", label: "Relevance" },
    { key: "content_depth", label: "Content Depth" },
    { key: "clarity_structure", label: "Clarity & Structure" },
    { key: "confidence_delivery", label: "Confidence Delivery" },
];

// Props for ReportScreen: the report data and the bottom button's action and label.
interface ReportScreenProps {
    summary: ReportSummary;
    onRestart: () => void;
    restartLabel?: string;
}

// Display the question, score, metrics, and tone for one answer.
function QuestionCard({ item, index }: { item: SessionResult; index: number }) {
    return (
        <div className="question-result">
            <h3>
                Q{index + 1}: {item.question}
                {item.question_type !== "General" && (
                    <span className="type-tag"> ({item.question_type})</span>
                )}
            </h3>
            <p className="transcript-preview">"{item.transcript}"</p>

            <div className="score-card-b">
                <ScoreRing
                    score={computeWeightedScore(item)}
                    size={96}
                    caption="Overall Score"
                />

                <div className="metrics-column">
                    {DIMENSIONS.map((d) => (
                        <MetricMeter
                            key={d.key}
                            label={d.label}
                            score={item.evaluation[d.key].score}
                            rationale={item.evaluation[d.key].rationale}
                        />
                    ))}
                    {item.eye_contact_score !== null &&
                        item.eye_contact_score !== undefined && (
                            <MetricMeter
                                label="Eye Contact"
                                score={item.eye_contact_score}
                            />
                        )}
                </div>
            </div>

            <div className="result-footer">
                <span className="metric-meter-label">Answer tone</span>
                <span className={`sentiment-tag ${item.sentiment.label}`}>
                    {toneLabel(item.sentiment.label)}
                </span>
            </div>
        </div>
    );
}

// Display the overall report and the result for each question.
export function ReportScreen({
    summary,
    onRestart,
    restartLabel = "Start Over",
}: ReportScreenProps) {
    return (
        <div className="screen">
            <h1>Final Report</h1>

            {summary.saved === true && (
                <p className="save-note save-note-good">
                    Saved to your history.
                </p>
            )}
            {summary.saved === false && (
                <p className="save-note">
                    Log in to save this result to your history.
                </p>
            )}

            <div className="summary-box">
                <h2>Overall Results</h2>

                <div className="score-card-b">
                    <ScoreRing score={summary.final_overall_score} />

                    <div className="metrics-column">
                        <MetricMeter
                            label="Relevance"
                            score={summary.avg_relevance}
                        />
                        <MetricMeter
                            label="Content Depth"
                            score={summary.avg_content_depth}
                        />
                        <MetricMeter
                            label="Clarity & Structure"
                            score={summary.avg_clarity_structure}
                        />
                        <MetricMeter
                            label="Confidence Delivery"
                            score={summary.avg_confidence_delivery}
                        />
                        {summary.avg_eye_contact !== null &&
                            summary.avg_eye_contact !== undefined && (
                                <MetricMeter
                                    label="Eye Contact"
                                    score={summary.avg_eye_contact}
                                />
                            )}
                    </div>
                </div>

                <div className="result-footer">
                    <span className="metric-meter-label">Answer tone</span>
                    <span
                        className={`sentiment-tag ${summary.dominant_sentiment}`}
                    >
                        {toneLabel(summary.dominant_sentiment)}
                    </span>
                </div>
            </div>

            <div id="report-questions">
                {summary.per_question.map((item, idx) => (
                    <QuestionCard item={item} index={idx} key={idx} />
                ))}
            </div>

            <button onClick={onRestart}>{restartLabel}</button>
        </div>
    );
}
