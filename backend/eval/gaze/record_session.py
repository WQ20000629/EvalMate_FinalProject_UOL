# ------------------------------------------------------------------
# File: backend/eval/gaze/record_session.py
# Purpose: Records webcam frames for the labeled gaze evaluation dataset.
# ------------------------------------------------------------------

"""Record a webcam gaze session, save the frames, and create the ground-truth labels."""
# Standard modules handle files, timing, and audio generation.
import csv
import os
import time

# OpenCV displays the webcam and NumPy creates the audio waveform.
import cv2
import numpy as np
import sounddevice as sd

# winsound.Beep made no sound on this machine, so the tone is generated
# with NumPy and played through the speakers instead.
def beep(freq, dur_ms):
    """Play a short tone to mark a recording transition."""
    # Build a sine wave at the given frequency and play it
    sr = 44100
    t = np.linspace(0, dur_ms / 1000, int(sr * dur_ms / 1000), False)
    tone = 0.4 * np.sin(freq * t * 2 * np.pi)
    sd.play(tone, sr)
    sd.wait()

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
FRAMES_DIR = os.path.join(HERE, "frames")
LABELS_CSV = os.path.join(HERE, "labels.csv")

# (condition, instruction text, duration seconds, expected_label)
# expected_label: "ON" means looking at the camera, "OFF" means looking away.
SEGMENTS = [
    ("camera_1", "LOOK AT THE CAMERA", 13, "ON"),
    ("down", "LOOK DOWN AT YOUR DESK", 13, "OFF"),
    ("camera_2", "LOOK AT THE CAMERA", 13, "ON"),
    ("side", "LOOK TO THE SIDE", 13, "OFF"),
    ("camera_3", "LOOK AT THE CAMERA", 13, "ON"),
    ("eyes_closed", "CLOSE YOUR EYES", 13, "OFF"),
    ("camera_4", "LOOK AT THE CAMERA", 13, "ON"),
    ("extreme_angle", "TURN YOUR HEAD SHARPLY AWAY", 13, "OFF"),
    ("camera_5", "LOOK AT THE CAMERA", 13, "ON"),
]

CAPTURE_HZ = 5  # frames saved per second per segment


def draw_overlay(frame, text, sub, color=(255, 255, 255)):
    """Draw the current instruction and timer over the webcam frame."""
    # Darken a strip at the top of the frame so the text is readable
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 90), (0, 0, 0), -1)
    frame[:] = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
    cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)
    cv2.putText(frame, sub, (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)


def main():
    """Record labeled webcam frames for the gaze evaluation dataset."""
    # Create the output folder and open the default webcam.
    os.makedirs(FRAMES_DIR, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("FAILED: could not open webcam.")
        return

    # Let auto-exposure settle.
    for _ in range(15):
        cap.read()

    rows = []
    frame_idx = 0
    aborted = False

    WIN = "Gaze recording"
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.moveWindow(WIN, 100, 100)
    cv2.resizeWindow(WIN, 640, 480)
    try:
        cv2.setWindowProperty(WIN, cv2.WND_PROP_TOPMOST, 1)
    except Exception:
        pass

    # Record each scripted gaze condition in order.
    for condition, text, duration, expected_label in SEGMENTS:
        # Low beep: previous segment just ended, open your eyes / face the screen again.
        beep(600, 150)

        # "Get ready" pause before this segment starts.
        ready_until = time.time() + 3
        while time.time() < ready_until:
            ok, frame = cap.read()
            if not ok:
                continue
            remaining = ready_until - time.time()
            draw_overlay(frame, f"NEXT: {text}", f"starting in {remaining:0.1f}s", color=(0, 220, 255))
            cv2.imshow(WIN, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                aborted = True
                break
        if aborted:
            break

        # High beep: segment starts now - perform the instructed action.
        beep(1000, 200)

        seg_start = time.time()
        next_capture = seg_start
        interval = 1.0 / CAPTURE_HZ
        last_tick = None

        # Capture frames at the selected rate until the segment ends.
        while time.time() - seg_start < duration:
            ok, frame = cap.read()
            if not ok:
                continue
            now = time.time()
            remaining = duration - (now - seg_start)
            draw_overlay(frame, text, f"{remaining:0.1f}s remaining  |  segment: {condition}", color=(0, 255, 120))
            cv2.imshow(WIN, frame)

            # Tick once a second in the final 3 seconds so the end of the segment
            # is heard when the screen is out of view (eyes closed or looking away).
            tick = int(remaining) if remaining <= 3 else None
            if tick is not None and tick != last_tick:
                beep(800, 80)
                last_tick = tick

            # Save a frame each time the capture interval has passed
            if now >= next_capture:
                fname = f"frame_{frame_idx:04d}.jpg"
                cv2.imwrite(os.path.join(FRAMES_DIR, fname), frame)
                rows.append({"frame_file": fname, "condition": condition, "expected_label": expected_label})
                frame_idx += 1
                next_capture += interval

            if cv2.waitKey(1) & 0xFF == ord("q"):
                aborted = True
                break
        if aborted:
            break

    cap.release()
    cv2.destroyAllWindows()

    if not rows:
        print("No frames captured (aborted immediately).")
        return

    # Save the frame names and their expected labels for later scoring.
    with open(LABELS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["frame_file", "condition", "expected_label"])
        writer.writeheader()
        writer.writerows(rows)

    status = "ABORTED EARLY" if aborted else "complete"
    print(f"Recording {status}. {len(rows)} frames captured to {FRAMES_DIR}")
    print(f"Ground-truth labels saved to {LABELS_CSV}")


if __name__ == "__main__":
    main()
