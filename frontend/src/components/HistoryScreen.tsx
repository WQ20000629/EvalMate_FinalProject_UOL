// ------------------------------------------------------------------
// File: frontend/src/components/HistoryScreen.tsx
// Purpose: Displays saved interview sessions and lets users open them.
// ------------------------------------------------------------------

// React hooks load and store the saved sessions.
import { useEffect, useState } from "react";
// Types and API function used by the history screen.
import type { SessionSummary } from "../types";
import { listSessions } from "../api";

// Props for HistoryScreen: callbacks to open a session or start a new one.
interface HistoryScreenProps {
    onSelectSession: (id: number) => void;
    onNewInterview: () => void;
}

// Display saved interviews and let the user open one or start a new interview.
export function HistoryScreen({
    onSelectSession,
    onNewInterview,
}: HistoryScreenProps) {
    const [sessions, setSessions] = useState<SessionSummary[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Load the user's sessions when this screen is opened.
    useEffect(() => {
        listSessions()
            .then(setSessions)
            .catch((e) =>
                setError(
                    e instanceof Error ? e.message : "Failed to load history.",
                ),
            );
    }, []);

    return (
        <div className="screen">
            <h1>Your Past Interviews</h1>

            {error && <p className="error">{error}</p>}
            {!error && sessions === null && (
                <p className="subtitle">Loading...</p>
            )}
            {sessions !== null && sessions.length === 0 && (
                <p className="subtitle">
                    No past sessions yet, complete an interview while logged in
                    to see it here.
                </p>
            )}

            {sessions !== null && sessions.length > 0 && (
                <div className="history-list">
                    {sessions.map((s) => (
                        <button
                            key={s.id}
                            type="button"
                            className="history-card"
                            onClick={() => onSelectSession(s.id)}
                        >
                            <div className="history-card-top">
                                <span className="history-card-date">
                                    {new Date(
                                        s.created_at,
                                    ).toLocaleDateString()}
                                </span>
                                <span className="history-card-score">
                                    {s.final_overall_score.toFixed(1)}/10
                                </span>
                            </div>
                            <p className="history-card-jd">
                                {s.job_description.slice(0, 140)}
                                {s.job_description.length > 140 ? "…" : ""}
                            </p>
                            <div className="history-card-bottom">
                                <span className="type-tag">
                                    {s.question_count} question
                                    {s.question_count === 1 ? "" : "s"}
                                </span>
                                <span
                                    className={`sentiment-tag ${s.dominant_sentiment}`}
                                >
                                    {s.dominant_sentiment}
                                </span>
                            </div>
                        </button>
                    ))}
                </div>
            )}

            <button type="button" onClick={onNewInterview}>
                New Interview
            </button>
        </div>
    );
}
