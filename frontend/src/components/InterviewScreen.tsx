import { useEffect } from "react";
import type { Question } from "../types";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useGazeTracking } from "../hooks/useGazeTracking";

interface InterviewScreenProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
  onSubmitAnswer: (transcript: string, eyeContactScore: number | null) => void;
  error: string | null;
}

export function InterviewScreen({
  question,
  questionNumber,
  totalQuestions,
  onSubmitAnswer,
  error,
}: InterviewScreenProps) {
  const audio = useAudioRecorder();
  const gaze = useGazeTracking();

  // Reset recording/gaze state whenever a new question is loaded.
  useEffect(() => {
    audio.reset();
    gaze.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question]);

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

  const handleSubmitClick = () => {
    if (audio.transcript) {
      onSubmitAnswer(audio.transcript, gaze.gazeScore);
    }
  };

  const recordLabel = audio.recordingActive
    ? "⏹ Stop Recording"
    : audio.hasRecording
      ? "🔁 Re-record"
      : "🎤 Start Recording";

  const badgeText =
    gaze.isLooking === null ? "👁 Detecting..." : gaze.isLooking ? "👁 Eye contact ✓" : "👁 Look at camera";
  const badgeBackground =
    gaze.isLooking === null
      ? "rgba(0,0,0,0.7)"
      : gaze.isLooking
        ? "rgba(21, 128, 61, 0.85)"
        : "rgba(185, 28, 28, 0.85)";

  const displayError = audio.error ?? error;

  return (
    <div className="screen">
      <h1>AI Interview Evaluator</h1>
      <p className="subtitle">
        Question {questionNumber} of {totalQuestions}
      </p>

      {question.type && question.type !== "General" && <div className="type-box">{question.type}</div>}

      <div className="question-box">
        <p>{question.question}</p>
      </div>

      <div id="cam-wrap" className={gaze.isTracking ? "" : "hidden"}>
        <video id="cam-feed" ref={gaze.videoRef} autoPlay muted playsInline />
        <div className="eye-live-badge" style={{ background: badgeBackground }}>
          {badgeText}
        </div>
      </div>

      <div className="recorder">
        <button id="btn-record" onClick={handleRecordClick} className={audio.recordingActive ? "recording" : ""}>
          {recordLabel}
        </button>
        <span id="record-status">{audio.statusText}</span>
      </div>

      {audio.transcript && (
        <div id="transcript-box">
          <p className="label">Transcript</p>
          <p>{audio.transcript}</p>
        </div>
      )}

      {audio.transcript && <button onClick={handleSubmitClick}>Submit Answer</button>}

      {displayError && <p className="error">{displayError}</p>}
    </div>
  );
}
