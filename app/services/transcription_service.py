from app.models.whisper_loader import get_model


class TranscriptionService:
    def __init__(self):
        self.model = get_model()

    def transcribe(self, audio_path: str):
        """
        Transcribe an audio file using Whisper.
        """

        result = self.model.transcribe(audio_path)

        return {
            "text": result["text"].strip(),
            "language": result["language"]
        }