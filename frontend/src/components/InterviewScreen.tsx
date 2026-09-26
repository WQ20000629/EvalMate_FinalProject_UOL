// ------------------------------------------------------------------
// File: frontend/src/components/InterviewScreen.tsx
// Purpose: Shows interview questions and manages recording and submission.
// ------------------------------------------------------------------

// React hooks manage the transcript editor and question changes.
import { useEffect, useState } from "react";
// Question type and browser recording/tracking hooks.
import type { Question } from "../types";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useGazeTracking } from "../hooks/useGazeTracking";

// Props for InterviewScreen: the current question, progress, and submit callback.
interface InterviewScreenProps {
    question: Question;
    questionNumber: number;
    totalQuestions: number;
    onSubmitAnswer: (
        transcript: string,
        eyeContactScore: number | null,
    ) => void;
    error: string | null;
}

// Let the user record an answer, check the transcript, and submit it.
export function InterviewScreen({
    question,
    questionNumber,
    totalQuestions,
    onSubmitAnswer,
    error,
}: InterviewScreenProps) {
    // Microphone recording and webcam gaze tracking for this answer.
    const audio = useAudioRecorder();
    const gaze = useGazeTracking();

    const [isEditingTranscript, setIsEditingTranscript] = useState(false);
    const [editedTranscript, setEditedTranscript] = useState("");

    // Reset recording and gaze state whenever a new question is loaded.
    useEffect(() => {
        audio.reset();
        gaze.stop();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [question]);

    // Turn off the microphone and webcam when leaving the interview screen.
    const { cancelRecording } = audio;
    const { stop: stopGaze } = gaze;
    useEffect(() => {
        return () => {
            cancelRecording();
            stopGaze();
        };
    }, [cancelRecording, stopGaze]);

    // Copy each new transcript into the editable text area.
    useEffect(() => {
        setEditedTranscript(audio.transcript ?? "");
        setIsEditingTranscript(false);
    }, [audio.transcript]);

    // Start or stop both recording and gaze tracking.
    const handleRecordClick = async () => {
        if (audio.recordingActive) {
            audio.stopRecording();
            gaze.stop();
        } else {
            const started = await audio.startRecording();
            if (started) {
                await gaze.start();
            }
        }
    };

    // Submit the edited transcript and the gaze score.
    const handleSubmitClick = () => {
        const finalTranscript = editedTranscript.trim();
        if (finalTranscript) {
            onSubmitAnswer(finalTranscript, gaze.gazeScore);
        }
    };

    // Change the record button text to match its current state.
    const recordLabel = audio.recordingActive
        ? "⏹ Stop Recording"
        : audio.hasRecording
          ? "🔁 Re-record"
          : "🎤 Start Recording";

    // Show the current eye-contact status over the camera preview.
    const badgeText =
        gaze.isLooking === null
            ? "👁 Detecting..."
            : gaze.isLooking
              ? "👁 Eye contact ✓"
              : "👁 Look at camera";
    const badgeBackground =
        gaze.isLooking === null
            ? "rgba(0,0,0,0.7)"
            : gaze.isLooking
              ? "rgba(21, 128, 61, 0.85)"
              : "rgba(185, 28, 28, 0.85)";

    const displayError = audio.error ?? error;

    return (
        <div className="screen">
            <h1>EvalMate</h1>
            <p className="subtitle">
                Question {questionNumber} of {totalQuestions}
            </p>

            {question.type && question.type !== "General" && (
                <div className="type-box">{question.type}</div>
            )}

            <div className="question-box">
                <p>{question.question}</p>
            </div>

            <div id="cam-wrap" className={gaze.isTracking ? "" : "hidden"}>
                <video
                    id="cam-feed"
                    ref={gaze.videoRef}
                    autoPlay
                    muted
                    playsInline
                />
                <div
                    className="eye-live-badge"
                    style={{ background: badgeBackground }}
                >
                    {badgeText}
                </div>
            </div>

            <div className="recorder">
                <button
                    id="btn-record"
                    onClick={handleRecordClick}
                    className={audio.recordingActive ? "recording" : ""}
                >
                    {recordLabel}
                </button>
                <span id="record-status">{audio.statusText}</span>
            </div>

            {audio.transcript && (
                <div id="transcript-box">
                    <div className="transcript-box-head">
                        <p className="label">Transcript</p>
                        <button
                            type="button"
                            className="btn-edit-transcript"
                            onClick={() =>
                                setIsEditingTranscript((prev) => !prev)
                            }
                        >
                            {isEditingTranscript ? "Done" : "✏️ Edit"}
                        </button>
                    </div>
                    {isEditingTranscript ? (
                        <textarea
                            className="transcript-edit"
                            value={editedTranscript}
                            onChange={(e) =>
                                setEditedTranscript(e.target.value)
                            }
                            rows={4}
                            autoFocus
                        />
                    ) : (
                        <p>{editedTranscript}</p>
                    )}
                </div>
            )}

            {audio.transcript && (
                <button
                    onClick={handleSubmitClick}
                    disabled={!editedTranscript.trim()}
                >
                    Submit Answer
                </button>
            )}

            {displayError && <p className="error">{displayError}</p>}
        </div>
    );
}
