from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel

from app.schemas.common import IntentType, TaskPriority, TaskStatus
from app.schemas.note_schema import NoteResponse
from app.schemas.task_schema import TaskResponse


class ExtractedIntent(BaseModel):
    intent: IntentType
    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    priority: TaskPriority | None = None
    task_identifier: str | None = None
    new_status: TaskStatus | None = None
    filters: dict[str, Any] | None = None


class ActionResult(BaseModel):
    type: str
    task: TaskResponse | None = None


class TranscribeResponse(BaseModel):
    note: NoteResponse
    intent: IntentType
    action: ActionResult
