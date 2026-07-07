import whisper
import torch

# Select GPU if available, otherwise CPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading Whisper model on {DEVICE}...")

# Load the model only once
model = whisper.load_model("base", device=DEVICE)

print("Whisper model loaded successfully!")


def get_model():
    """
    Return the loaded Whisper model.
    """
    return model