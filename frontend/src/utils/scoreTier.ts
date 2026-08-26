export type ScoreTier = "good" | "warning" | "critical";

export function getScoreTier(score: number): ScoreTier {
  if (score >= 9) return "good";
  if (score >= 6) return "warning";
  return "critical";
}

// Vivid mark color - for ring/bar fills only. Never used for text (contrast).
const TIER_FILL: Record<ScoreTier, string> = {
  good: "#0ca30c",
  warning: "#fab219",
  critical: "#d03b3b",
};

// Darker, readable variant - for icons and text that sit beside the mark.
const TIER_TEXT: Record<ScoreTier, string> = {
  good: "oklch(35% 0.1 145)",
  warning: "#8a5c08",
  critical: "oklch(40% 0.14 25)",
};

const TIER_BADGE_BG: Record<ScoreTier, string> = {
  good: "oklch(90% 0.08 145)",
  warning: "oklch(96% 0.05 85)",
  critical: "oklch(90% 0.07 25)",
};

const OVERALL_COMMENT: Record<ScoreTier, string> = {
  good: "Excellent, you're interview ready!",
  warning: "Good, room to grow",
  critical: "Needs more practice",
};

export function getScoreFill(score: number): string {
  return TIER_FILL[getScoreTier(score)];
}

export function getScoreText(score: number): string {
  return TIER_TEXT[getScoreTier(score)];
}

export function getScoreBadgeBg(score: number): string {
  return TIER_BADGE_BG[getScoreTier(score)];
}

export function getOverallComment(score: number): string {
  return OVERALL_COMMENT[getScoreTier(score)];
}
