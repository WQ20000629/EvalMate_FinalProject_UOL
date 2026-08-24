# Import necessary libraries
import whisper

class Transcriber:
    """
    Handles audio-to-text transcription using the Whisper model.
    This class loads a Whisper model and provides a simple method
    to convert audio files into text transcripts.
    """
    def __init__(self, model_size="base"):
        """
        Initialise the transcriber with a base Whisper model.
        """
        self.size = model_size
        self.whisper_model = whisper.load_model(model_size)

    def transcribe(self, audio_file):
        """
        Transcribe an audio file into text.
        Returns:
            str: Transcribed text from the audio.
        """
        output = self.whisper_model.transcribe(audio_file, language="en")
        return output["text"].strip()
