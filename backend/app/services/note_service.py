import json as json_module
from datetime import date

from fastapi import HTTPException

from app.models.note import Note
from app.models.task import Task
from app.repositories.note_repository import NoteRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.common import IntentType, NoteSource, TaskPriority, TaskStatus
from app.schemas.note_schema import NoteResponse, PaginatedNoteResponse
from app.schemas.task_schema import TaskResponse
from app.schemas.voice_schema import ActionResult, IntentAction, TranscribeResponse
from app.services.embedding_service import EmbeddingService
from app.services.intent_service import IntentService


class NoteService:
    def __init__(
        self,
        note_repo: NoteRepository,
        task_repo: TaskRepository,
        intent_service: IntentService,
        embedding: EmbeddingService,
    ) -> None:
        self._note_repo = note_repo
        self._task_repo = task_repo
        self._intent = intent_service
        self._embedding = embedding

    async def _embed_task(self, task: Task, title: str, description: str | None) -> None:
        task.embedding = await self._embedding.embed(
            EmbeddingService.embed_text(title, description)
        )

    async def create_from_transcript(
        self, transcript: str, source: str
    ) -> TranscribeResponse:
        extracted = await self._intent.extract_intent(transcript)
        action_results: list[ActionResult] = []
        all_note_tasks: list[Task] = []

        for action in extracted.actions:
            task_responses: list[TaskResponse] = []

            if action.intent == IntentType.CREATE_TASK and action.tasks:
                seen: set[str] = set()
                for task_intent in action.tasks:
                    key = task_intent.title.strip().lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    task = Task(
                        title=task_intent.title,
                        description=task_intent.description,
                        status=TaskStatus.PENDING.value,
                        priority=task_intent.priority.value if task_intent.priority else None,
                        due_date=task_intent.due_date,
                    )
                    await self._embed_task(task, task_intent.title, task_intent.description)
                    created = await self._task_repo.create(task)
                    all_note_tasks.append(created)
                    task_responses.append(TaskResponse.model_validate(created))

            elif action.intent == IntentType.UPDATE_TASK_STATUS:
                task_responses, task_objs = await self._handle_update_status(action)
                all_note_tasks.extend(task_objs)

            elif action.intent == IntentType.QUERY_TASKS:
                task_responses, task_objs = await self._handle_query(action)
                all_note_tasks.extend(task_objs)

            action_results.append(ActionResult(intent=action.intent, tasks=task_responses))

        seen_task_ids: set[str] = set()
        unique_note_tasks: list[Task] = []
        for t in all_note_tasks:
            if t.id not in seen_task_ids:
                seen_task_ids.add(t.id)
                unique_note_tasks.append(t)

        note = Note(
            raw_transcript=transcript,
            source=source,
            tasks=unique_note_tasks,
            actions_json=json_module.dumps(
                [a.model_dump(mode="json") for a in action_results]
            ),
        )
        created_note = await self._note_repo.create(note)

        return TranscribeResponse(
            note=NoteResponse.model_validate(created_note),
            actions=action_results,
        )

    async def _handle_update_status(
        self, action: IntentAction
    ) -> tuple[list[TaskResponse], list[Task]]:
        if not action.task_identifier:
            return [], []
        if not action.new_status and not action.new_due_date:
            return [], []

        query_embedding = await self._embedding.embed(action.task_identifier)
        matches = await self._task_repo.semantic_search(query_embedding, limit=3)

        if matches and action.task_due_date:
            matches = [m for m in matches if m.due_date == action.task_due_date]

        if not matches:
            matches = await self._task_repo.search_by_title(
                action.task_identifier,
                due_date=action.task_due_date,
            )

        if not matches:
            task = Task(
                title=action.task_identifier,
                status=action.new_status.value if action.new_status else TaskStatus.PENDING.value,
                due_date=action.new_due_date,
            )
            await self._embed_task(task, action.task_identifier, None)
            created = await self._task_repo.create(task)
            return [TaskResponse.model_validate(created)], [created]

        task = matches[0]
        if action.new_status:
            task.status = action.new_status.value
        if action.new_due_date:
            task.due_date = action.new_due_date
        updated = await self._task_repo.save(task)
        return [TaskResponse.model_validate(updated)], [updated]

    async def _handle_query(
        self, action: IntentAction
    ) -> tuple[list[TaskResponse], list[Task]]:
        f = action.filters
        keyword = f.keyword if f else None
        status = TaskStatus(f.status.value) if f and f.status else None
        priority = TaskPriority(f.priority.value) if f and f.priority else None
        due_before = f.due_before if f else None
        due_after = f.due_after if f else None
        items, _ = await self._task_repo.list(
            keyword=keyword,
            status=status,
            priority=priority,
            due_before=due_before,
            due_after=due_after,
            page=1,
            page_size=10,
        )
        return [TaskResponse.model_validate(t) for t in items], list(items)

    async def get_note(self, note_id: str) -> NoteResponse:
        note = await self._note_repo.find_by_id(note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found")
        return NoteResponse.model_validate(note)

    async def list_notes(
        self,
        source: NoteSource | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedNoteResponse:
        items, total = await self._note_repo.list(
            source=source.value if source else None,
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
