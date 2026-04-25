from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.repositories.note_repository import NoteRepository
from app.repositories.task_repository import TaskRepository
from app.services.embedding_service import EmbeddingService
from app.services.intent_service import IntentService
from app.services.note_service import NoteService
from app.services.stt_service import STTService
from app.services.task_service import TaskService

# Module-level singletons — populated by init_services() called from lifespan.
# Avoids re-constructing expensive objects (OpenAI client, Whisper model) per request.
_intent_service: IntentService | None = None
_stt_service: STTService | None = None
_embedding_service: EmbeddingService | None = None


def init_services() -> None:
    global _intent_service, _stt_service, _embedding_service
    _intent_service = IntentService()
    _stt_service = STTService()
    _embedding_service = EmbeddingService()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_task_repository(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


def get_intent_service() -> IntentService:
    assert _intent_service is not None, "Services not initialised — call init_services() in lifespan"
    return _intent_service


def get_stt_service() -> STTService:
    assert _stt_service is not None, "Services not initialised — call init_services() in lifespan"
    return _stt_service


def get_embedding_service() -> EmbeddingService:
    assert _embedding_service is not None, "Services not initialised — call init_services() in lifespan"
    return _embedding_service


def get_task_service(
    repo: TaskRepository = Depends(get_task_repository),
    embedding: EmbeddingService = Depends(get_embedding_service),
) -> TaskService:
    return TaskService(repo, embedding)


def get_note_service(
    db: AsyncSession = Depends(get_db),
    intent_service: IntentService = Depends(get_intent_service),
    embedding: EmbeddingService = Depends(get_embedding_service),
) -> NoteService:
    return NoteService(NoteRepository(db), TaskRepository(db), intent_service, embedding)
