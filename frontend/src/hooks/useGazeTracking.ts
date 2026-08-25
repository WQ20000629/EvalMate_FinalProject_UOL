import { useCallback, useRef, useState } from "react";

// FaceMesh/Camera load as globals from the CDN <script> tags in index.html
// (see MediaPipe's own docs - there's no first-party npm+bundler story for
// these that's simpler than the classic <script> tag).
declare global {
  interface Window {
    FaceMesh: new (config: { locateFile: (file: string) => string }) => FaceMeshInstance;
    Camera: new (
      videoEl: HTMLVideoElement,
      config: { onFrame: () => Promise<void>; width: number; height: number }
    ) => CameraInstance;
  }
}

interface Landmark {
  x: number;
  y: number;
}

interface FaceMeshResults {
  multiFaceLandmarks?: Landmark[][];
}

interface FaceMeshInstance {
  setOptions: (opts: Record<string, unknown>) => void;
  onResults: (cb: (results: FaceMeshResults) => void) => void;
  send: (input: { image: HTMLVideoElement }) => Promise<void>;
}

interface CameraInstance {
  start: () => Promise<void>;
  stop: () => void;
}

function hRatio(a: Landmark, b: Landmark, iris: Landmark): number {
  const lo = Math.min(a.x, b.x);
  const hi = Math.max(a.x, b.x);
  const w = hi - lo;
  if (w < 0.001) return 0.5;
  return (iris.x - lo) / w;
}

function vRatio(top: Landmark, bot: Landmark, iris: Landmark): number {
  const lo = Math.min(top.y, bot.y);
  const hi = Math.max(top.y, bot.y);
  const h = hi - lo;
  if (h < 0.001) return 0.5;
  return (iris.y - lo) / h;
}

export function useGazeTracking() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const faceMeshRef = useRef<FaceMeshInstance | null>(null);
  const cameraRef = useRef<CameraInstance | null>(null);
  const runningRef = useRef(false);
  const okFramesRef = useRef(0);
  const totalFramesRef = useRef(0);

  const [isTracking, setIsTracking] = useState(false);
  const [isLooking, setIsLooking] = useState<boolean | null>(null);
  const [gazeScore, setGazeScore] = useState<number | null>(null);

  const onResults = useCallback((data: FaceMeshResults) => {
    if (!runningRef.current) return;
    totalFramesRef.current++;

    const lm = data.multiFaceLandmarks?.[0];
    if (!lm) {
      setIsLooking(false);
      return;
    }

    // Iris landmarks missing (refineLandmarks failed this frame) - accept as fallback.
    if (lm.length < 474) {
      okFramesRef.current++;
      setIsLooking(true);
      return;
    }

    try {
      const hl = hRatio(lm[33], lm[133], lm[468]);
      const hr = hRatio(lm[263], lm[362], lm[473]);
      const vl = vRatio(lm[159], lm[145], lm[468]);
      const vr = vRatio(lm[386], lm[374], lm[473]);

      const leftOk = hl >= 0.35 && hl <= 0.65 && vl >= 0.2 && vl <= 0.55;
      const rightOk = hr >= 0.35 && hr <= 0.65 && vr >= 0.2 && vr <= 0.55;

      if (leftOk && rightOk) okFramesRef.current++;
      setIsLooking(leftOk && rightOk);
    } catch {
      setIsLooking(false);
    }
  }, []);

  const start = useCallback(async () => {
    okFramesRef.current = 0;
    totalFramesRef.current = 0;
    setGazeScore(null);
    runningRef.current = true;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;

      const videoEl = videoRef.current;
      if (!videoEl) throw new Error("video element not mounted");

      videoEl.srcObject = stream;
      await new Promise<void>((resolve) => {
        videoEl.onloadedmetadata = () => resolve();
      });
      await videoEl.play();

      if (!faceMeshRef.current) {
        const faceMesh = new window.FaceMesh({
          locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`,
        });
        faceMesh.setOptions({
          maxNumFaces: 1,
          refineLandmarks: true,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5,
        });
        faceMesh.onResults(onResults);
        faceMeshRef.current = faceMesh;
      }

      const camera = new window.Camera(videoEl, {
        onFrame: async () => {
          if (runningRef.current && faceMeshRef.current) {
            await faceMeshRef.current.send({ image: videoEl });
          }
        },
        width: 640,
        height: 480,
      });
      cameraRef.current = camera;
      await camera.start();

      setIsTracking(true);
    } catch {
      runningRef.current = false;
      setIsTracking(false);
    }
  }, [onResults]);

  const stop = useCallback(() => {
    runningRef.current = false;
    setIsTracking(false);
    setIsLooking(null);

    if (cameraRef.current) {
      cameraRef.current.stop();
      cameraRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    const score =
      totalFramesRef.current > 0
        ? Math.round((okFramesRef.current / totalFramesRef.current) * 100) / 10
        : null;
    setGazeScore(score);
  }, []);

  return { videoRef, isTracking, isLooking, gazeScore, start, stop };
}
