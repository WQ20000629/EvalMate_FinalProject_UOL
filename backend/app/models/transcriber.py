import whisper


class Transcriber:
    def __init__(self, model_size="base"):
        self.size = model_size
        self.whisper_model = whisper.load_model(model_size)

    def transcribe(self, audio_file):
        output = self.whisper_model.transcribe(audio_file, language="en")
        return output["text"].strip()
