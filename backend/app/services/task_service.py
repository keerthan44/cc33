import asyncio
import logging
from datetime import date

from fastapi import HTTPException

from app.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.common import TaskPriority, TaskStatus
from app.schemas.task_schema import (
    PaginatedTaskResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task] = set()


def _fire_background(coro) -> None:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


class TaskService:
    def __init__(self, repository: TaskRepository, embedding: EmbeddingService) -> None:
        self._repo = repository
        self._embedding = embedding

    async def create_task(self, data: TaskCreate) -> TaskResponse:
        task = Task(
            title=data.title,
            description=data.description,
            status=data.status.value,
            priority=data.priority.value if data.priority else None,
            due_date=data.due_date,
        )
        created = await self._repo.create(task)
        _fire_background(
            self._embedding.embed_task_background(
                created.id, EmbeddingService.embed_text(data.title, data.description)
            )
        )
        return TaskResponse.model_validate(created)

    async def get_task(self, task_id: str) -> TaskResponse:
        task = await self._repo.find_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskResponse.model_validate(task)

    async def list_tasks(
        self,
        keyword: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_before: date | None = None,
        due_after: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedTaskResponse:
        items, total = await self._repo.list(
            keyword=keyword,
            status=status,
            priority=priority,
            due_before=due_before,
            due_after=due_after,
            page=page,
            page_size=page_size,
        )
        return PaginatedTaskResponse(
            items=[TaskResponse.model_validate(t) for t in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_task(self, task_id: str, data: TaskUpdate) -> TaskResponse:
        task = await self._repo.find_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        title_changed = data.title is not None and data.title != task.title
        desc_changed = data.description is not None and data.description != task.description
        for field, value in data.model_dump(mode="json", exclude_none=True).items():
            setattr(task, field, value)
        updated = await self._repo.save(task)
        if title_changed or desc_changed:
            _fire_background(
                self._embedding.embed_task_background(
                    updated.id,
                    EmbeddingService.embed_text(updated.title, updated.description),
                )
            )
        return TaskResponse.model_validate(updated)

    async def delete_task(self, task_id: str) -> None:
        task = await self._repo.find_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        await self._repo.delete(task)
