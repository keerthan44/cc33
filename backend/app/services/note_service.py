from datetime import date

from fastapi import HTTPException

from app.models.note import Note
from app.models.task import Task
from app.repositories.note_repository import NoteRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.common import IntentType, TaskStatus
from app.schemas.note_schema import NoteResponse, PaginatedNoteResponse
from app.schemas.task_schema import TaskResponse
from app.schemas.voice_schema import ActionResult, ExtractedIntent, TranscribeResponse
from app.services.intent_service import IntentService


class NoteService:
    def __init__(
        self,
        note_repo: NoteRepository,
        task_repo: TaskRepository,
        intent_service: IntentService,
    ) -> None:
        self._note_repo = note_repo
        self._task_repo = task_repo
        self._intent = intent_service

    async def create_from_transcript(
        self, transcript: str, source: str
    ) -> TranscribeResponse:
        intent: ExtractedIntent = await self._intent.extract_intent(transcript)
        task_response: TaskResponse | None = None

        if intent.intent == IntentType.CREATE_TASK and intent.title:
            task = Task(
                title=intent.title,
                description=intent.description,
                status=TaskStatus.PENDING.value,
                priority=intent.priority.value if intent.priority else None,
                due_date=intent.due_date,
            )
            created_task = await self._task_repo.create(task)
            task_response = TaskResponse.model_validate(created_task)

        note = Note(
            raw_transcript=transcript,
            source=source,
            task_id=task_response.id if task_response else None,
        )
        created_note = await self._note_repo.create(note)

        return TranscribeResponse(
            note=NoteResponse.model_validate(created_note),
            intent=intent.intent,
            action=ActionResult(type=intent.intent.value, task=task_response),
        )

    async def get_note(self, note_id: str) -> NoteResponse:
        note = await self._note_repo.find_by_id(note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found")
        return NoteResponse.model_validate(note)

    async def list_notes(
        self,
        source: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedNoteResponse:
        items, total = await self._note_repo.list(
            source=source,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
        return PaginatedNoteResponse(
            items=[NoteResponse.model_validate(n) for n in items],
            total=total,
            page=page,
            page_size=page_size,
        )
