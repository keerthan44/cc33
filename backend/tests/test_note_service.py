import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.common import IntentType
from app.schemas.voice_schema import ExtractedIntent, IntentAction, TaskIntent
from app.services.note_service import NoteService


def _make_task(title: str = "Task", task_id: str | None = None):
    from app.models.task import Task
    t = MagicMock(spec=Task)
    t.id = task_id or str(uuid.uuid4())
    t.title = title
    t.description = None
    t.status = "PENDING"
    t.priority = None
    t.due_date = None
    return t


def _make_note(task_id: str | None = None, tasks=None):
    from app.models.note import Note
    n = MagicMock(spec=Note)
    n.id = str(uuid.uuid4())
    n.raw_transcript = "test"
    n.source = "voice"
    n.task_id = task_id
    n.tasks = tasks or []
    n.actions_json = None
    return n


def _make_service(intent_result: ExtractedIntent, created_tasks=None, query_tasks=None):
    note_repo = AsyncMock()
    task_repo = AsyncMock()
    intent_service = AsyncMock()
    embedding = AsyncMock()
    embedding.embed_task_background = AsyncMock()
    embedding.embed = AsyncMock(return_value=[0.0] * 1536)

    intent_service.extract_intent.return_value = intent_result

    if created_tasks:
        task_repo.create.side_effect = created_tasks
    if query_tasks is not None:
        task_repo.list.return_value = (query_tasks, len(query_tasks))
        task_repo.semantic_search.return_value = []

    note_repo.create.side_effect = lambda n: (
        setattr(n, "id", str(uuid.uuid4())) or n
    )

    return NoteService(note_repo, task_repo, intent_service, embedding)


class TestCreateFromTranscript:
    @pytest.mark.asyncio
    async def test_create_task_intent_creates_tasks(self):
        fake_task = _make_task("Buy groceries")
        service = _make_service(
            ExtractedIntent(actions=[
                IntentAction(intent=IntentType.CREATE_TASK, tasks=[TaskIntent(title="Buy groceries")])
            ]),
            created_tasks=[fake_task],
        )
        with patch("app.services.note_service._fire_background"):
            result = await service.create_from_transcript("Buy groceries", "voice")

        service._task_repo.create.assert_called_once()
        assert len(result.actions) == 1
        assert result.actions[0].intent == IntentType.CREATE_TASK
        assert result.actions[0].tasks[0].title == "Buy groceries"

    @pytest.mark.asyncio
    async def test_general_note_creates_no_tasks(self):
        service = _make_service(
            ExtractedIntent(actions=[IntentAction(intent=IntentType.GENERAL_NOTE)])
        )
        result = await service.create_from_transcript("Just a note", "voice")

        service._task_repo.create.assert_not_called()
        assert result.actions[0].intent == IntentType.GENERAL_NOTE

    @pytest.mark.asyncio
    async def test_deduplicates_tasks_with_same_id(self):
        """Overlapping QUERY actions returning the same task must not create duplicate note_tasks rows."""
        shared_id = str(uuid.uuid4())
        fake_task = _make_task("Dentist", task_id=shared_id)

        service = _make_service(
            ExtractedIntent(actions=[
                IntentAction(intent=IntentType.QUERY_TASKS),
                IntentAction(intent=IntentType.QUERY_TASKS),
            ]),
            query_tasks=[fake_task],
        )
        result = await service.create_from_transcript("dentist tasks", "voice")

        note_passed = service._note_repo.create.call_args[0][0]
        task_ids = [t.id for t in note_passed.tasks]
        assert len(task_ids) == len(set(task_ids)), "Duplicate task IDs in note.tasks"

    @pytest.mark.asyncio
    async def test_duplicate_task_titles_are_deduplicated(self):
        """Two TaskIntents with the same normalised title should only create one task."""
        fake_task = _make_task("dentist")
        service = _make_service(
            ExtractedIntent(actions=[
                IntentAction(
                    intent=IntentType.CREATE_TASK,
                    tasks=[
                        TaskIntent(title="dentist"),
                        TaskIntent(title="Dentist"),  # same normalised
                    ],
                )
            ]),
            created_tasks=[fake_task],
        )
        with patch("app.services.note_service._fire_background"):
            result = await service.create_from_transcript("dentist", "voice")

        assert service._task_repo.create.call_count == 1
        assert len(result.actions[0].tasks) == 1

    @pytest.mark.asyncio
    async def test_multi_intent_returns_all_action_results(self):
        fake_task = _make_task("Doctor")
        note_repo = AsyncMock()
        task_repo = AsyncMock()
        intent_svc = AsyncMock()
        embedding = AsyncMock()
        embedding.embed = AsyncMock(return_value=[0.0] * 1536)
        embedding.embed_task_background = AsyncMock()
        task_repo.create.return_value = fake_task
        task_repo.list.return_value = ([fake_task], 1)
        task_repo.semantic_search.return_value = []
        intent_svc.extract_intent.return_value = ExtractedIntent(actions=[
            IntentAction(intent=IntentType.CREATE_TASK, tasks=[TaskIntent(title="Doctor")]),
            IntentAction(intent=IntentType.QUERY_TASKS),
        ])
        note_repo.create.side_effect = lambda n: (setattr(n, "id", str(uuid.uuid4())) or n)

        service = NoteService(note_repo, task_repo, intent_svc, embedding)
        with patch("app.services.note_service._fire_background"):
            result = await service.create_from_transcript("add doctor and list tasks", "voice")

        assert len(result.actions) == 2
        intents = {a.intent for a in result.actions}
        assert IntentType.CREATE_TASK in intents
        assert IntentType.QUERY_TASKS in intents
