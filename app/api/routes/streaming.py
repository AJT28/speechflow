import asyncio
import json
import os
import tempfile

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.transcription_service import TranscriptionService

router = APIRouter(tags=["Live Transcription"])

transcription_service = TranscriptionService()

# The browser sends one chunk every two seconds.
# Three chunks means transcription occurs approximately every six seconds.
CHUNKS_PER_TRANSCRIPTION = 3


@router.websocket("/ws/transcribe")
async def live_transcription(websocket: WebSocket) -> None:
    await websocket.accept()

    audio_buffer = bytearray()
    chunks_received = 0
    previous_text = ""

    await websocket.send_json(
        {
            "status": "connected",
            "message": "Live transcription started",
        }
    )

    try:
        while True:
            message = await websocket.receive()

            # Binary message: microphone audio
            if message.get("bytes") is not None:
                audio_chunk = message["bytes"]

                audio_buffer.extend(audio_chunk)
                chunks_received += 1

                await websocket.send_json(
                    {
                        "status": "buffering",
                        "bytes": len(audio_buffer),
                        "chunks": chunks_received,
                    }
                )

                if chunks_received % CHUNKS_PER_TRANSCRIPTION == 0:
                    transcript = await transcribe_buffer(
                        bytes(audio_buffer)
                    )
                    print("Partial transcript result:", transcript)

                    text = transcript.get("text", "").strip()

                    if text and text != previous_text:
                        previous_text = text

                        await websocket.send_json(
                            {
                                "status": "transcribing",
                                "text": text,
                                "language": transcript.get("language"),
                                "final": False,
                            }
                        )

            # Text message: commands such as stop
            elif message.get("text") is not None:
                command = parse_command(message["text"])

                if command == "stop":
                    if audio_buffer:
                        transcript = await transcribe_buffer(
                            bytes(audio_buffer)
                        )
                        print("Final transcript result:", transcript)
                        await websocket.send_json(
                            {
                                "status": "completed",
                                "text": transcript.get(
                                    "text",
                                    "",
                                ).strip(),
                                "language": transcript.get("language"),
                                "final": True,
                            }
                        )

                    await websocket.close()
                    break

    except WebSocketDisconnect:
        print("Live transcription client disconnected")

    except Exception as error:
        print(f"Live transcription error: {error}")

        try:
            await websocket.send_json(
                {
                    "status": "error",
                    "error": str(error),
                }
            )
        except Exception:
            pass


async def transcribe_buffer(
    audio_data: bytes,
) -> dict[str, str]:
    """
    Save the accumulated browser audio as a temporary WebM file
    and run Whisper without blocking FastAPI's event loop.
    """

    temp_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm",
        ) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name

        result = await asyncio.to_thread(
            transcription_service.transcribe,
            temp_path,
        )

        return result

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def parse_command(raw_message: str) -> str | None:
    try:
        data = json.loads(raw_message)
        return data.get("event")
    except json.JSONDecodeError:
        return raw_message
    
