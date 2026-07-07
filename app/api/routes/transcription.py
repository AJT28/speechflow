import os
import tempfile

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.services.transcription_service import TranscriptionService

router = APIRouter(
    tags=["Transcription"],
)

service = TranscriptionService()


@router.post(
    "/transcribe",
    summary="Transcribe audio file",
    description="""
Upload an audio file and receive a speech-to-text transcription.

Supported formats:
- `.wav`
- `.mp3`
- `.m4a`
- `.flac`

The model runs on GPU if CUDA is available.
    """,
)
async def transcribe(file: UploadFile = File(...)):
    allowed_extensions = [".wav", ".mp3", ".m4a", ".flac"]
    suffix = os.path.splitext(file.filename)[1].lower()

    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Use wav, mp3, m4a, or flac.",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        return service.transcribe(temp_path)
    finally:
        os.remove(temp_path)