from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.common import IntentType, TaskPriority, TaskStatus
from app.schemas.note_schema import NoteResponse
from app.schemas.task_schema import TaskResponse


class TaskQueryFilters(BaseModel):
    """Filters for QUERY_TASKS intent. All fields are optional and combinable.

    `keyword` drives a partial-text search on task titles so the user can say
    "show me the dentist task" without knowing the exact title — the DB returns
    the closest match and the result can be used to drive a follow-up update.
    """

    model_config = ConfigDict(extra="forbid")

    keyword: str | None = None      # partial title match — ILIKE %keyword%
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_before: str | None = None   # YYYY-MM-DD upper bound
    due_after: str | None = None    # YYYY-MM-DD lower bound


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
