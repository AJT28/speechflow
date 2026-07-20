import asyncio
import os
import tempfile
from typing import Any

from app.services.transcription_service import TranscriptionService


class StreamingTranscriptionService:
    """
    Manages audio buffering and live transcription.
    """

    def __init__(
        self,
        transcription_service: TranscriptionService,
        chunks_per_transcription: int = 3,
    ) -> None:
        self.transcription_service = transcription_service
        self.chunks_per_transcription = chunks_per_transcription

        self.audio_buffer = bytearray()
        self.chunks_received = 0
        self.previous_text = ""

    def add_audio_chunk(self, audio_chunk: bytes) -> None:
        """
        Add a microphone audio chunk to the current buffer.
        """

        self.audio_buffer.extend(audio_chunk)
        self.chunks_received += 1

    def should_transcribe(self) -> bool:
        """
        Return True when enough chunks have been received.
        """

        return (
            self.chunks_received > 0
            and self.chunks_received
            % self.chunks_per_transcription
            == 0
        )

    def has_audio(self) -> bool:
        return bool(self.audio_buffer)

    def get_buffer_size(self) -> int:
        return len(self.audio_buffer)

    def get_chunks_received(self) -> int:
        return self.chunks_received

    async def create_partial_transcript(
        self,
    ) -> dict[str, Any] | None:
        """
        Transcribe the accumulated audio and return a result only
        when the text has changed.
        """

        result = await self._transcribe_current_buffer()

        text = result.get("text", "").strip()

        if not text or text == self.previous_text:
            return None

        self.previous_text = text

        return {
            "text": text,
            "language": result.get("language"),
        }

    async def create_final_transcript(
        self,
    ) -> dict[str, Any]:
        """
        Transcribe the complete audio buffer.
        """

        if not self.has_audio():
            return {
                "text": "",
                "language": None,
            }

        result = await self._transcribe_current_buffer()

        return {
            "text": result.get("text", "").strip(),
            "language": result.get("language"),
        }

    async def _transcribe_current_buffer(
        self,
    ) -> dict[str, Any]:
        """
        Save buffered audio temporarily and run Whisper without
        blocking FastAPI's event loop.
        """

        temp_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".webm",
            ) as temp_file:
                temp_file.write(bytes(self.audio_buffer))
                temp_path = temp_file.name

            result = await asyncio.to_thread(
                self.transcription_service.transcribe,
                temp_path,
            )

            return result

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)