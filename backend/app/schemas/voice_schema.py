from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.common import IntentType, TaskPriority, TaskStatus
from app.schemas.note_schema import NoteResponse
from app.schemas.task_schema import TaskResponse


class TaskQueryFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keyword: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_before: date | None = None
    due_after: date | None = None


class TaskIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    due_date: date | None = None
    priority: TaskPriority | None = None


class IntentAction(BaseModel):
    """A single intent extracted from the transcript. Multiple may appear in one utterance."""

    model_config = ConfigDict(extra="forbid")

    intent: IntentType
    tasks: list[TaskIntent] = []
    task_identifier: str | None = None
    task_due_date: date | None = None   # disambiguator: identifies WHICH task
    new_status: TaskStatus | None = None
    new_due_date: date | None = None    # the new due date to set (for reschedule/postpone)
    filters: TaskQueryFilters | None = None


class ExtractedIntent(BaseModel):
    """Structured LLM output. extra='forbid' satisfies OpenAI strict-mode schema requirements."""

    model_config = ConfigDict(extra="forbid")

    actions: list[IntentAction]


class ActionResult(BaseModel):
    intent: IntentType
    tasks: list[TaskResponse] = []


class TranscribeResponse(BaseModel):
    note: NoteResponse
    actions: list[ActionResult]
