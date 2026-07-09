# from app.models.whisper_loader import get_model
import whisper
import torch

# Select GPU if available, otherwise CPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class TranscriptionService:
    def __init__(self):
        self.model = whisper.load_model("base", device=DEVICE)

    def transcribe(self, audio_path: str):
        """
        Transcribe an audio file using Whisper.
        """

        result = self.model.transcribe(audio_path)

        return {
            "text": result["text"].strip(),
            "language": result["language"]
        }