from __future__ import annotations

import json as json_module
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import NoteSource
from app.schemas.task_schema import TaskResponse


class NoteCreate(BaseModel):
    raw_transcript: str
    source: NoteSource = NoteSource.TEXT


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    raw_transcript: str
    source: NoteSource
    created_at: datetime
    tasks: list[TaskResponse] = []
    actions_json: str | None = Field(default=None, exclude=True)
    note_actions: list[dict[str, Any]] = []

    @model_validator(mode="after")
    def parse_note_actions(self) -> "NoteResponse":
        if self.actions_json and not self.note_actions:
            try:
                self.note_actions = json_module.loads(self.actions_json)
            except Exception:
                pass
        return self


class PaginatedNoteResponse(BaseModel):
    items: list[NoteResponse]
    total: int
    page: int
    page_size: int
