from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.task_schema import TaskResponse


class NoteCreate(BaseModel):
    raw_transcript: str
    source: str = "text"


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    raw_transcript: str
    source: str
    created_at: datetime
    task: TaskResponse | None = None


class PaginatedNoteResponse(BaseModel):
    items: list[NoteResponse]
    total: int
    page: int
    page_size: int
