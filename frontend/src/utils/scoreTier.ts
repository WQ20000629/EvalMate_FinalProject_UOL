// ------------------------------------------------------------------
// File: frontend/src/utils/scoreTier.ts
// Purpose: Converts scores into colours, icons, and feedback messages.
// ------------------------------------------------------------------

// Possible visual states used by the score components.
export type ScoreTier = "good" | "warning" | "critical";

// Turn a numeric score into a simple status tier for the UI.
export function getScoreTier(score: number): ScoreTier {
    if (score >= 9) return "good";
    if (score >= 6) return "warning";
    return "critical";
}

// Bright colours used for score rings and progress bars.
const TIER_FILL: Record<ScoreTier, string> = {
    good: "#0ca30c",
    warning: "#fab219",
    critical: "#d03b3b",
};

// Darker colours used for text and icons.
const TIER_TEXT: Record<ScoreTier, string> = {
    good: "oklch(35% 0.1 145)",
    warning: "#8a5c08",
    critical: "oklch(40% 0.14 25)",
};

// Light background colours used for score badges.
const TIER_BADGE_BG: Record<ScoreTier, string> = {
    good: "oklch(90% 0.08 145)",
    warning: "oklch(96% 0.05 85)",
    critical: "oklch(90% 0.07 25)",
};

// Short feedback message shown below a score.
const OVERALL_COMMENT: Record<ScoreTier, string> = {
    good: "Excellent, you're interview ready!",
    warning: "Good, room to grow",
    critical: "Needs more practice",
};

// Get the fill colour for a score.
export function getScoreFill(score: number): string {
    return TIER_FILL[getScoreTier(score)];
}

// Get the readable text colour for a score.
export function getScoreText(score: number): string {
    return TIER_TEXT[getScoreTier(score)];
}

// Get the badge background colour for a score.
export function getScoreBadgeBg(score: number): string {
    return TIER_BADGE_BG[getScoreTier(score)];
}

// Get the short feedback message for a score.
export function getOverallComment(score: number): string {
    return OVERALL_COMMENT[getScoreTier(score)];
}
