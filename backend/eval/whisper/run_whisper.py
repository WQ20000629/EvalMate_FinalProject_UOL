# ------------------------------------------------------------------
# File: backend/eval/whisper/run_whisper.py
# Purpose: Runs Whisper on test audio clips and saves the transcripts.
# ------------------------------------------------------------------

"""Run Whisper on each clip and save the transcripts for WER evaluation."""
# Standard modules load clip details, handle model options, and save results.
import argparse
import csv
import json
import os
import sys
import time

# The application transcriber runs Whisper on each audio file.
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from app.models.transcriber import Transcriber

# Paths to the files this script reads and writes
HERE = os.path.dirname(__file__)
CLIPS_DIR = os.path.join(HERE, "clips")
GROUND_TRUTH_CSV = os.path.join(HERE, "ground_truth.csv")


def load_clip_rows():
    """Load the audio clips listed in the ground-truth file."""
    with open(GROUND_TRUTH_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    """Transcribe every available clip with the selected Whisper model."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-size", default="base", help="Whisper model size, e.g. base, small")
    args = parser.parse_args()

    rows = load_clip_rows()
    if not rows:
        print("No rows found in ground_truth.csv. Nothing to transcribe.")
        return

    print(f"Loading Whisper model '{args.model_size}'...")
    transcriber = Transcriber(model_size=args.model_size)

    # Store each transcript and the time taken to produce it.
    results = []
    for row in rows:
        clip_id = row["clip_id"]
        audio_path = os.path.join(CLIPS_DIR, row["audio_file"])

        if not os.path.exists(audio_path):
            print(f"  [SKIP] {clip_id}: audio file not found at {audio_path}")
            continue

        # Transcribe the clip and measure the processing time.
        print(f"  Transcribing {clip_id}...")
        start = time.time()
        transcript = transcriber.transcribe(audio_path)
        elapsed = round(time.time() - start, 2)

        results.append({
            "clip_id": clip_id,
            "audio_file": row["audio_file"],
            "condition": row["condition"],
            "length": row["length"],
            "whisper_transcript": transcript,
            "transcribe_seconds": elapsed,
        })
        print(f"    -> {elapsed}s | {transcript[:80]}{'...' if len(transcript) > 80 else ''}")

    # Save results using the model name so different model sizes can be compared.
    out_path = os.path.join(HERE, f"results_{args.model_size}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. {len(results)}/{len(rows)} clips transcribed. Results saved to {out_path}")


if __name__ == "__main__":
    main()
