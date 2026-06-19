import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.models.transcriber import Transcriber

def main():
    audio_path = input("Enter path to an audio file to test: ").strip()

    print("Loading Whisper model... ")
    transcriber = Transcriber(model_size="base")

    print("Transcribing...")
    text = transcriber.transcribe(audio_path)

    print("\n--- TRANSCRIPT ---")
    print(text)


if __name__ == "__main__":
    main()