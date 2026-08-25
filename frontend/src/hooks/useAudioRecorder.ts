import { useCallback, useRef, useState } from "react";
import { transcribeAudio } from "../api";

export function useAudioRecorder() {
  const recorderRef = useRef<MediaRecorder | null>(null);
  const audioBufferRef = useRef<Blob[]>([]);

  const [recordingActive, setRecordingActive] = useState(false);
  const [hasRecording, setHasRecording] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [transcript, setTranscript] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startRecording = useCallback(async (): Promise<boolean> => {
    setError(null);
    try {
      const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioBufferRef.current = [];
      setTranscript(null);

      const recorder = new MediaRecorder(micStream);
      recorder.ondataavailable = (e) => audioBufferRef.current.push(e.data);
      recorder.onstop = async () => {
        micStream.getTracks().forEach((t) => t.stop());
        setStatusText("Transcribing...");

        const clip = new Blob(audioBufferRef.current, { type: "audio/webm" });
        try {
          const text = await transcribeAudio(clip);
          if (!text || !text.trim()) {
            setError("No speech detected. Please try recording again.");
            setStatusText("");
            return;
          }
          setTranscript(text);
          setHasRecording(true);
          setStatusText("Done.");
        } catch (e) {
          setError(`Transcription failed: ${e instanceof Error ? e.message : "Unknown error"}`);
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

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    setRecordingActive(false);
    setStatusText("Processing...");
  }, []);

  const reset = useCallback(() => {
    setRecordingActive(false);
    setHasRecording(false);
    setStatusText("");
    setTranscript(null);
    setError(null);
    audioBufferRef.current = [];
  }, []);

  return { recordingActive, hasRecording, statusText, transcript, error, startRecording, stopRecording, reset };
}
