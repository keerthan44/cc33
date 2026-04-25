import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.dependencies import get_note_service, get_stt_service
from app.schemas.common import NoteSource
from app.schemas.voice_schema import TranscribeResponse
from app.services.note_service import NoteService
from app.services.stt_service import STTService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])

_partial_tasks: set[asyncio.Task] = set()


@router.post("/transcribe", response_model=TranscribeResponse, status_code=200)
async def transcribe_upload(
    file: UploadFile,
    stt: STTService = Depends(get_stt_service),
    note_service: NoteService = Depends(get_note_service),
) -> TranscribeResponse:
    audio_bytes = await file.read()
    if len(audio_bytes) > settings.MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio file too large")
    transcript = await stt.transcribe(audio_bytes)
    return await note_service.create_from_transcript(transcript, NoteSource.VOICE.value)


@router.websocket("/stream")
async def voice_stream(
    websocket: WebSocket,
    stt: STTService = Depends(get_stt_service),
    note_service: NoteService = Depends(get_note_service),
) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "ready"})

    chunks: list[bytes] = []
    stop_received: bool = False
    is_transcribing: list[bool] = [False]
    # True when a chunk arrived while Whisper was busy; triggers a re-run
    # with the latest accumulated audio as soon as Whisper finishes.
    pending: list[bool] = [False]
    total_bytes: int = 0

    async def send_partial(audio: bytes) -> None:
        try:
            logger.debug("Partial transcription started (%d bytes)", len(audio))
            text = await stt.transcribe(audio, vad_filter=True)
            if text:
                logger.debug("Partial transcript: %s", text)
                try:
                    await websocket.send_json({"type": "partial", "text": text})
                except Exception as exc:
                    logger.warning("Failed to send partial transcript: %s", exc)
            else:
                logger.debug("Partial transcription returned empty (VAD filtered or silence)")
        except Exception as exc:
            logger.error("Partial transcription error: %s", exc)
        finally:
            is_transcribing[0] = False
            # If new chunks arrived while we were busy, immediately process
            # the latest snapshot rather than waiting for the next chunk.
            if pending[0] and not stop_received:
                pending[0] = False
                is_transcribing[0] = True
                task = asyncio.create_task(send_partial(b"".join(chunks)))
                _partial_tasks.add(task)
                task.add_done_callback(_partial_tasks.discard)

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                chunk: bytes = message["bytes"]
                chunks.append(chunk)
                total_bytes += len(chunk)
                if total_bytes > settings.MAX_AUDIO_BYTES:
                    await websocket.send_json({"type": "error", "message": "Audio too large"})
                    break
                if not is_transcribing[0] and not stop_received:
                    is_transcribing[0] = True
                    task = asyncio.create_task(send_partial(b"".join(chunks)))
                    _partial_tasks.add(task)
                    task.add_done_callback(_partial_tasks.discard)
                elif is_transcribing[0]:
                    pending[0] = True
            elif "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "stop" and not stop_received:
                    stop_received = True
                    combined = b"".join(chunks)
                    final_text = await stt.transcribe(combined, vad_filter=False)
                    result = await note_service.create_from_transcript(final_text, NoteSource.VOICE.value)
                    await websocket.send_json({"type": "final", "transcript": final_text})
                    await websocket.send_json({"type": "note", "note": result.note.model_dump(mode="json")})
                    await websocket.send_json({
                        "type": "actions",
                        "actions": [a.model_dump(mode="json") for a in result.actions],
                    })
                    await websocket.send_json({"type": "done"})
                    break
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
