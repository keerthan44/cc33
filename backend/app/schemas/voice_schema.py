from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.common import IntentType, TaskPriority, TaskStatus
from app.schemas.note_schema import NoteResponse
from app.schemas.task_schema import TaskResponse


class TaskQueryFilters(BaseModel):
    """Typed filters for QUERY_TASKS intent — keeps OpenAI strict-mode happy."""

    model_config = ConfigDict(extra="forbid")

    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_before: str | None = None
    due_after: str | None = None


class ExtractedIntent(BaseModel):
    """Structured LLM output. extra='forbid' satisfies OpenAI strict-mode schema requirements."""

    model_config = ConfigDict(extra="forbid")

    intent: IntentType
    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    priority: TaskPriority | None = None
    task_identifier: str | None = None
    new_status: TaskStatus | None = None
    filters: TaskQueryFilters | None = None


class ActionResult(BaseModel):
    type: str
    task: TaskResponse | None = None


class TranscribeResponse(BaseModel):
    note: NoteResponse
    intent: IntentType
    action: ActionResult
