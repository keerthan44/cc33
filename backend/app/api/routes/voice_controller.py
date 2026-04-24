import json
import logging

from fastapi import APIRouter, Depends, UploadFile, WebSocket, WebSocketDisconnect

from app.core.dependencies import get_note_service, get_stt_service
from app.schemas.voice_schema import TranscribeResponse
from app.services.note_service import NoteService
from app.services.stt_service import STTService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe", response_model=TranscribeResponse, status_code=200)
async def transcribe_upload(
    file: UploadFile,
    stt: STTService = Depends(get_stt_service),
    note_service: NoteService = Depends(get_note_service),
) -> TranscribeResponse:
    audio_bytes = await file.read()
    transcript = await stt.transcribe(audio_bytes)
    return await note_service.create_from_transcript(transcript, "voice")


@router.websocket("/stream")
async def voice_stream(
    websocket: WebSocket,
    stt: STTService = Depends(get_stt_service),
    note_service: NoteService = Depends(get_note_service),
) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "ready"})
    chunks: list[bytes] = []
    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                chunk: bytes = message["bytes"]
                chunks.append(chunk)
                partial = await stt.transcribe(chunk, vad_filter=True)
                if partial:
                    await websocket.send_json({"type": "partial", "text": partial})
            elif "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "stop":
                    combined = b"".join(chunks)
                    final_text = await stt.transcribe(combined, vad_filter=False)
                    result = await note_service.create_from_transcript(final_text, "voice")
                    await websocket.send_json({"type": "final", "transcript": final_text})
                    await websocket.send_json({"type": "intent", "intent": result.intent.value})
                    await websocket.send_json({
                        "type": "note",
                        "note": result.note.model_dump(mode="json"),
                    })
                    if result.action.task:
                        await websocket.send_json({
                            "type": "task",
                            "task": result.action.task.model_dump(mode="json"),
                        })
                    await websocket.send_json({"type": "done"})
                    break
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
