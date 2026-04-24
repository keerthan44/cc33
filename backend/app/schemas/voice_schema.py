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


class TaskIntent(BaseModel):
    """A single task extracted from the transcript. Multiple may appear in one utterance."""

    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    due_date: date | None = None
    priority: TaskPriority | None = None


class ExtractedIntent(BaseModel):
    """Structured LLM output. extra='forbid' satisfies OpenAI strict-mode schema requirements."""

    model_config = ConfigDict(extra="forbid")

    intent: IntentType
    tasks: list[TaskIntent] = []         # one or more tasks for CREATE_TASK
    task_identifier: str | None = None   # keyword identifying which task to update
    task_due_date: date | None = None    # optional due-date disambiguator for UPDATE_TASK_STATUS
    new_status: TaskStatus | None = None
    filters: TaskQueryFilters | None = None


class ActionResult(BaseModel):
    type: str
    tasks: list[TaskResponse] = []


class TranscribeResponse(BaseModel):
    note: NoteResponse
    intent: IntentType
    action: ActionResult
