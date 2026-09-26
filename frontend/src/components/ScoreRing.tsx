// ------------------------------------------------------------------
// File: frontend/src/components/ScoreRing.tsx
// Purpose: Displays an interview score as a coloured circular ring.
// ------------------------------------------------------------------

// Score helpers determine the ring colour, text colour, and feedback.
import {
    getScoreFill,
    getScoreText,
    getScoreBadgeBg,
    getOverallComment,
    getScoreTier,
} from "../utils/scoreTier";
import { TierIcon } from "./TierIcon";

// Props for ScoreRing: the score out of 10, ring size in pixels, and caption text.
interface ScoreRingProps {
    score: number;
    size?: number;
    caption?: string;
}

// Display a score as a circular progress ring with feedback.
export function ScoreRing({
    score,
    size = 130,
    caption = "Final Weighted Score",
}: ScoreRingProps) {
    // Ring thickness and radius scale with the ring size.
    const strokeWidth = size * 0.09;
    const radius = (size - strokeWidth) / 2 - 2;
    const circumference = 2 * Math.PI * radius;
    // Convert the score out of 10 into a safe progress value from 0 to 1.
    const pct = Math.max(0, Math.min(1, score / 10));
    // Hide the unfilled part of the ring by offsetting the dashed stroke.
    const offset = circumference * (1 - pct);
    const center = size / 2;

    const tier = getScoreTier(score);
    const fill = getScoreFill(score);

    return (
        <div className="score-ring-block">
            <div
                className="score-ring-wrap"
                style={{ width: size, height: size }}
            >
                <svg
                    width={size}
                    height={size}
                    viewBox={`0 0 ${size} ${size}`}
                    className="score-ring-svg"
                >
                    <circle
                        cx={center}
                        cy={center}
                        r={radius}
                        fill="none"
                        stroke="var(--ring-track)"
                        strokeWidth={strokeWidth}
                    />
                    <circle
                        cx={center}
                        cy={center}
                        r={radius}
                        fill="none"
                        stroke={fill}
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                    />
                </svg>
                <div className="score-ring-value">
                    <span className="score-ring-number">
                        {score.toFixed(1)}
                    </span>
                    <span className="score-ring-out-of">/ 10</span>
                </div>
            </div>

            <span className="score-ring-caption">{caption}</span>

            <div
                className="score-comment"
                style={{
                    background: getScoreBadgeBg(score),
                    color: getScoreText(score),
                }}
            >
                <TierIcon tier={tier} size={12} />
                <span>{getOverallComment(score)}</span>
            </div>
        </div>
    );
}
