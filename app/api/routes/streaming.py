import json

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from app.services.streaming_service import (
    StreamingTranscriptionService,
)
from app.services.transcription_service import (
    TranscriptionService,
)


router = APIRouter(tags=["Live Transcription"])


@router.websocket("/ws/transcribe")
async def live_transcription(
    websocket: WebSocket,
) -> None:
    await websocket.accept()

    transcription_service = TranscriptionService()

    streaming_service = StreamingTranscriptionService(
        transcription_service=transcription_service,
        chunks_per_transcription=3,
    )

    await websocket.send_json(
        {
            "status": "connected",
            "message": "Live transcription started",
        }
    )

    try:
        while True:
            message = await websocket.receive()

            if message.get("bytes") is not None:
                await handle_audio_message(
                    websocket=websocket,
                    streaming_service=streaming_service,
                    audio_chunk=message["bytes"],
                )

            elif message.get("text") is not None:
                should_stop = await handle_text_message(
                    websocket=websocket,
                    streaming_service=streaming_service,
                    raw_message=message["text"],
                )

                if should_stop:
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


async def handle_audio_message(
    websocket: WebSocket,
    streaming_service: StreamingTranscriptionService,
    audio_chunk: bytes,
) -> None:
    streaming_service.add_audio_chunk(audio_chunk)

    await websocket.send_json(
        {
            "status": "buffering",
            "bytes": streaming_service.get_buffer_size(),
            "chunks": (
                streaming_service.get_chunks_received()
            ),
        }
    )

    if not streaming_service.should_transcribe():
        return

    transcript = (
        await streaming_service.create_partial_transcript()
    )

    print("Partial transcript result:", transcript)

    if transcript is None:
        return

    await websocket.send_json(
        {
            "status": "transcribing",
            "text": transcript["text"],
            "language": transcript["language"],
            "final": False,
        }
    )


async def handle_text_message(
    websocket: WebSocket,
    streaming_service: StreamingTranscriptionService,
    raw_message: str,
) -> bool:
    command = parse_command(raw_message)

    if command != "stop":
        return False

    transcript = (
        await streaming_service.create_final_transcript()
    )

    print("Final transcript result:", transcript)

    await websocket.send_json(
        {
            "status": "completed",
            "text": transcript["text"],
            "language": transcript["language"],
            "final": True,
        }
    )

    await websocket.close()

    return True


def parse_command(
    raw_message: str,
) -> str | None:
    try:
        data = json.loads(raw_message)

        if isinstance(data, dict):
            return data.get("event")

        return None

    except json.JSONDecodeError:
        return raw_message