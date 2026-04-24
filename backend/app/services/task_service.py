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


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repo = repository

    async def create_task(self, data: TaskCreate) -> TaskResponse:
        task = Task(
            title=data.title,
            description=data.description,
            status=data.status.value,
            priority=data.priority.value if data.priority else None,
            due_date=data.due_date,
        )
        created = await self._repo.create(task)
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
        for field, value in data.model_dump(exclude_none=True).items():
            if field == "status" and isinstance(value, TaskStatus):
                task.status = value.value
            elif field == "priority" and isinstance(value, TaskPriority):
                task.priority = value.value
            else:
                setattr(task, field, value)
        updated = await self._repo.save(task)
        return TaskResponse.model_validate(updated)

    async def delete_task(self, task_id: str) -> None:
        task = await self._repo.find_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        await self._repo.delete(task)
