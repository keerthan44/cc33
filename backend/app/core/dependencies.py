from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.repositories.note_repository import NoteRepository
from app.repositories.task_repository import TaskRepository
from app.services.intent_service import IntentService
from app.services.note_service import NoteService
from app.services.stt_service import STTService
from app.services.task_service import TaskService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_task_repository(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


def get_note_repository(db: AsyncSession = Depends(get_db)) -> NoteRepository:
    return NoteRepository(db)


def get_intent_service() -> IntentService:
    return IntentService()


def get_stt_service() -> STTService:
    return STTService()


def get_task_service(
    repo: TaskRepository = Depends(get_task_repository),
) -> TaskService:
    return TaskService(repo)


def get_note_service(
    note_repo: NoteRepository = Depends(get_note_repository),
    task_repo: TaskRepository = Depends(get_task_repository),
    intent_service: IntentService = Depends(get_intent_service),
) -> NoteService:
    return NoteService(note_repo, task_repo, intent_service)
