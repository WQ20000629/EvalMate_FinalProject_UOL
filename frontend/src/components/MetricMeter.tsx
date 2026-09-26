// ------------------------------------------------------------------
// File: frontend/src/components/MetricMeter.tsx
// Purpose: Displays one interview metric with its score and feedback.
// ------------------------------------------------------------------

// Score helpers provide the colour and icon for this metric.
import { getScoreFill, getScoreText, getScoreTier } from "../utils/scoreTier";
import { TierIcon } from "./TierIcon";

// Props for MetricMeter. Rationale is only passed for per-question metrics.
interface MetricMeterProps {
    label: string;
    score: number;
    rationale?: string;
}

// Show one metric as a bar with its score, plus the rationale when one is passed.
export function MetricMeter({ label, score, rationale }: MetricMeterProps) {
    const tier = getScoreTier(score);
    const fill = getScoreFill(score);
    // Keep the progress bar between 0 and 100 percent.
    const pct = Math.max(0, Math.min(100, (score / 10) * 100));

    return (
        <div className="metric-meter">
            <div className="metric-meter-head">
                <span className="metric-meter-label">{label}</span>
                <span className="metric-meter-value">
                    <span
                        className="metric-meter-icon"
                        style={{ color: getScoreText(score) }}
                    >
                        <TierIcon tier={tier} size={12} />
                    </span>
                    {score.toFixed(1)}
                </span>
            </div>
            <div className="metric-meter-track">
                <div
                    className="metric-meter-fill"
                    style={{ width: `${pct}%`, background: fill }}
                />
            </div>
            {rationale && <p className="metric-meter-rationale">{rationale}</p>}
        </div>
    );
}
