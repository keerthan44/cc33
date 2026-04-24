from datetime import date

from fastapi import HTTPException

from app.models.note import Note
from app.models.task import Task
from app.repositories.note_repository import NoteRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.common import IntentType, TaskPriority, TaskStatus
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
        task_responses: list[TaskResponse] = []

        if intent.intent == IntentType.CREATE_TASK and intent.tasks:
            for task_intent in intent.tasks:
                task = Task(
                    title=task_intent.title,
                    description=task_intent.description,
                    status=TaskStatus.PENDING.value,
                    priority=task_intent.priority.value if task_intent.priority else None,
                    due_date=task_intent.due_date,
                )
                created = await self._task_repo.create(task)
                task_responses.append(TaskResponse.model_validate(created))

        elif intent.intent == IntentType.UPDATE_TASK_STATUS:
            task_responses = await self._handle_update_status(intent)

        elif intent.intent == IntentType.QUERY_TASKS:
            task_responses = await self._handle_query(intent)

        note = Note(
            raw_transcript=transcript,
            source=source,
            task_id=task_responses[0].id if task_responses else None,
        )
        created_note = await self._note_repo.create(note)

        return TranscribeResponse(
            note=NoteResponse.model_validate(created_note),
            intent=intent.intent,
            action=ActionResult(type=intent.intent.value, tasks=task_responses),
        )

    async def _handle_update_status(
        self, intent: ExtractedIntent
    ) -> list[TaskResponse]:
        if not intent.task_identifier or not intent.new_status:
            return []
        matches = await self._task_repo.search_by_title(
            intent.task_identifier,
            due_date=intent.task_due_date,
        )
        if not matches:
            return []
        task = matches[0]
        task.status = intent.new_status.value
        updated = await self._task_repo.save(task)
        return [TaskResponse.model_validate(updated)]

    async def _handle_query(self, intent: ExtractedIntent) -> list[TaskResponse]:
        f = intent.filters
        status = TaskStatus(f.status.value) if f and f.status else None
        priority = TaskPriority(f.priority.value) if f and f.priority else None
        items, _ = await self._task_repo.list(
            status=status,
            priority=priority,
            page=1,
            page_size=10,
        )
        return [TaskResponse.model_validate(t) for t in items]

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
