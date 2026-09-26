# ------------------------------------------------------------------
# File: backend/eval/gaze/run_gaze_eval.py
# Purpose: Runs the gaze heuristic and compares it with the expected labels.
# ------------------------------------------------------------------

"""Run the gaze heuristic on all saved frames and compare it with the labels."""
# Standard modules load labels, predictions, and file paths.
import csv
import json
import os

# MediaPipe and OpenCV detect faces in the saved frames.
import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions, RunningMode

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
FRAMES_DIR = os.path.join(HERE, "frames")
LABELS_CSV = os.path.join(HERE, "labels.csv")
MODEL_PATH = os.path.join(HERE, "face_landmarker.task")
PREDICTIONS_JSON = os.path.join(HERE, "predictions.json")

# Mirrors useGazeTracking.ts thresholds exactly.
H_LO, H_HI = 0.35, 0.65
V_LO, V_HI = 0.20, 0.55
IRIS_LANDMARK_COUNT = 474  # lm.length < 474 => refineLandmarks failed this frame


def h_ratio(a, b, iris):
    """Measure the iris position across the horizontal eye width."""
    # 0 means the iris is at one corner of the eye, 1 means the other corner
    lo, hi = min(a.x, b.x), max(a.x, b.x)
    w = hi - lo
    if w < 0.001:
        return 0.5
    return (iris.x - lo) / w


def v_ratio(top, bot, iris):
    """Measure the iris position across the vertical eye height."""
    # 0 means the iris is at the top eyelid, 1 means the bottom eyelid
    lo, hi = min(top.y, bot.y), max(top.y, bot.y)
    h = hi - lo
    if h < 0.001:
        return 0.5
    return (iris.y - lo) / h


def classify(landmarks):
    """Reproduces onResults() in useGazeTracking.ts. Returns True/False (isLooking)."""
    if landmarks is None:
        return False  # no face detected this frame

    if len(landmarks) < IRIS_LANDMARK_COUNT:
        return True  # iris refinement failed -> accepted as fallback pass

    try:
        # Eye corner and eyelid landmarks for each eye, 468 and 473 are the iris centres
        hl = h_ratio(landmarks[33], landmarks[133], landmarks[468])
        hr = h_ratio(landmarks[263], landmarks[362], landmarks[473])
        vl = v_ratio(landmarks[159], landmarks[145], landmarks[468])
        vr = v_ratio(landmarks[386], landmarks[374], landmarks[473])

        # Both irises must be near the centre of the eye to count as looking
        left_ok = H_LO <= hl <= H_HI and V_LO <= vl <= V_HI
        right_ok = H_LO <= hr <= H_HI and V_LO <= vr <= V_HI
        return left_ok and right_ok
    except Exception:
        return False


def main():
    """Run FaceLandmarker on each labeled frame and save predictions."""
    # Read the expected gaze label for every saved frame.
    with open(LABELS_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("No labeled frames found. Run record_session.py first.")
        return

    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    # Detect landmarks and compare the heuristic result with the expected label.
    predictions = []
    with FaceLandmarker.create_from_options(options) as landmarker:
        for row in rows:
            frame_path = os.path.join(FRAMES_DIR, row["frame_file"])
            bgr = cv2.imread(frame_path)
            if bgr is None:
                print(f"WARNING: could not read {frame_path}, skipping.")
                continue

            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect(mp_image)

            landmarks = result.face_landmarks[0] if result.face_landmarks else None
            predicted_looking = classify(landmarks)
            expected_looking = row["expected_label"] == "ON"

            predictions.append({
                "frame_file": row["frame_file"],
                "condition": row["condition"],
                "expected_label": row["expected_label"],
                "face_detected": landmarks is not None,
                "landmark_count": len(landmarks) if landmarks is not None else 0,
                "predicted_looking": predicted_looking,
                "expected_looking": expected_looking,
                "correct": predicted_looking == expected_looking,
            })

    with open(PREDICTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    print(f"Evaluated {len(predictions)} frames. Predictions saved to {PREDICTIONS_JSON}")
    n_correct = sum(1 for p in predictions if p["correct"])
    print(f"Raw accuracy: {n_correct}/{len(predictions)} ({n_correct / len(predictions) * 100:.1f}%)")


if __name__ == "__main__":
    main()
