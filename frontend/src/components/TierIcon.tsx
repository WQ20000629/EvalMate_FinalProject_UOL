import type { ScoreTier } from "../utils/scoreTier";

interface TierIconProps {
  tier: ScoreTier;
  size?: number;
}

export function TierIcon({ tier, size = 13 }: TierIconProps) {
  if (tier === "good") {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <path
          d="M4 12.5l5 5L20 7"
          stroke="currentColor"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (tier === "warning") {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
        <path d="M12 8v5M12 16.5h.01" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      </svg>
    );
  }

  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M12 7.5v6M12 16.5h.01" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}
