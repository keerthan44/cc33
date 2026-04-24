from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_note_service
from app.schemas.note_schema import NoteCreate, NoteResponse, PaginatedNoteResponse
from app.schemas.voice_schema import TranscribeResponse
from app.services.note_service import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=TranscribeResponse, status_code=201)
async def create_note(
    body: NoteCreate,
    service: NoteService = Depends(get_note_service),
) -> TranscribeResponse:
    return await service.create_from_transcript(body.raw_transcript, body.source)


@router.get("", response_model=PaginatedNoteResponse, status_code=200)
async def list_notes(
    source: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: NoteService = Depends(get_note_service),
) -> PaginatedNoteResponse:
    return await service.list_notes(
        source=source, date_from=date_from, date_to=date_to,
        page=page, page_size=page_size,
    )


@router.get("/{note_id}", response_model=NoteResponse, status_code=200)
async def get_note(
    note_id: str,
    service: NoteService = Depends(get_note_service),
) -> NoteResponse:
    return await service.get_note(note_id)
