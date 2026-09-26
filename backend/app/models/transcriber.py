# ------------------------------------------------------------------
# File: backend/app/models/transcriber.py
# Purpose: Converts recorded interview audio into text using Whisper.
# ------------------------------------------------------------------

# Import the Whisper library used for audio transcription
import whisper


class Transcriber:
    """Convert an audio file into a text transcript using Whisper."""

    def __init__(self, model_size="base"):
        """Load the Whisper model for transcription."""
        self.size = model_size
        self.whisper_model = whisper.load_model(model_size)

    def transcribe(self, audio_file):
        """Return the text transcription for the given audio file."""
        output = self.whisper_model.transcribe(audio_file, language="en")
        return output["text"].strip()
