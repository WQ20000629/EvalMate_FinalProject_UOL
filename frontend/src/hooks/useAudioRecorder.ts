// ------------------------------------------------------------------
// File: frontend/src/hooks/useAudioRecorder.ts
// Purpose: Records microphone audio and sends it for transcription.
// ------------------------------------------------------------------

// React hooks store the recorder object and the current recording state.
import { useCallback, useRef, useState } from "react";
// API function used to convert the audio into text.
import { transcribeAudio } from "../api";

// Record an answer, send it for transcription, and expose its status.
export function useAudioRecorder() {
    const recorderRef = useRef<MediaRecorder | null>(null);
    const audioBufferRef = useRef<Blob[]>([]);

    const [recordingActive, setRecordingActive] = useState(false);
    const [hasRecording, setHasRecording] = useState(false);
    const [statusText, setStatusText] = useState("");
    const [transcript, setTranscript] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Start recording from the user's microphone.
    const startRecording = useCallback(async (): Promise<boolean> => {
        setError(null);
        try {
            const micStream = await navigator.mediaDevices.getUserMedia({
                audio: true,
            });
            audioBufferRef.current = [];
            setTranscript(null);

            const recorder = new MediaRecorder(micStream);
            // Store each audio chunk until recording stops.
            recorder.ondataavailable = (e) =>
                audioBufferRef.current.push(e.data);
            // Stop the microphone and send the finished clip for transcription.
            recorder.onstop = async () => {
                micStream.getTracks().forEach((t) => t.stop());
                setStatusText("Transcribing...");

                const clip = new Blob(audioBufferRef.current, {
                    type: "audio/webm",
                });
                try {
                    const text = await transcribeAudio(clip);
                    if (!text || !text.trim()) {
                        setError(
                            "No speech detected. Please try recording again.",
                        );
                        setStatusText("");
                        return;
                    }
                    setTranscript(text);
                    setHasRecording(true);
                    setStatusText("Done.");
                } catch (e) {
                    setError(
                        `Transcription failed: ${e instanceof Error ? e.message : "Unknown error"}`,
                    );
                    setStatusText("");
                }
            };

            recorder.start();
            recorderRef.current = recorder;
            setRecordingActive(true);
            setStatusText("Recording...");
            return true;
        } catch {
            setError("Microphone access denied. Please allow microphone use.");
            return false;
        }
    }, []);

    // Stop recording and begin processing the saved audio chunks.
    const stopRecording = useCallback(() => {
        if (recorderRef.current && recorderRef.current.state !== "inactive") {
            recorderRef.current.stop();
        }
        setRecordingActive(false);
        setStatusText("Processing...");
    }, []);

    // Clear the current recording and all related messages.
    const reset = useCallback(() => {
        setRecordingActive(false);
        setHasRecording(false);
        setStatusText("");
        setTranscript(null);
        setError(null);
        audioBufferRef.current = [];
    }, []);

    return {
        recordingActive,
        hasRecording,
        statusText,
        transcript,
        error,
        startRecording,
        stopRecording,
        reset,
    };
}
