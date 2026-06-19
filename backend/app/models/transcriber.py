import whisper

class Transcriber:
    """
    Wraps OpenAI's Whisper model for speech-to-text transcription.
    """

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribes an audio file to text.

        Args:
            audio_path: Path to the audio file

        Returns:
            The transcribed text as a string.
        """
        result = self.model.transcribe(audio_path, language="en")
        return result["text"].strip()