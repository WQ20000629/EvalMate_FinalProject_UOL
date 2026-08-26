import { getScoreFill, getScoreText, getScoreBadgeBg, getOverallComment, getScoreTier } from "../utils/scoreTier";
import { TierIcon } from "./TierIcon";

interface ScoreRingProps {
  score: number;
  size?: number;
  caption?: string;
}

export function ScoreRing({ score, size = 130, caption = "Final Weighted Score" }: ScoreRingProps) {
  const strokeWidth = size * 0.09;
  const radius = (size - strokeWidth) / 2 - 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(1, score / 10));
  const offset = circumference * (1 - pct);
  const center = size / 2;

  const tier = getScoreTier(score);
  const fill = getScoreFill(score);

  return (
    <div className="score-ring-block">
      <div className="score-ring-wrap" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="score-ring-svg">
          <circle cx={center} cy={center} r={radius} fill="none" stroke="var(--ring-track)" strokeWidth={strokeWidth} />
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
          <span className="score-ring-number">{score.toFixed(1)}</span>
          <span className="score-ring-out-of">/ 10</span>
        </div>
      </div>

      <span className="score-ring-caption">{caption}</span>

      <div className="score-comment" style={{ background: getScoreBadgeBg(score), color: getScoreText(score) }}>
        <TierIcon tier={tier} size={12} />
        <span>{getOverallComment(score)}</span>
      </div>
    </div>
  );
}
