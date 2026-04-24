from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_task_service
from app.schemas.common import TaskPriority, TaskStatus
from app.schemas.task_schema import PaginatedTaskResponse, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=PaginatedTaskResponse, status_code=200)
async def list_tasks(
    status: TaskStatus | None = Query(default=None),
    priority: TaskPriority | None = Query(default=None),
    due_before: date | None = Query(default=None),
    due_after: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: TaskService = Depends(get_task_service),
) -> PaginatedTaskResponse:
    return await service.list_tasks(
        status=status, priority=priority,
        due_before=due_before, due_after=due_after,
        page=page, page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskResponse, status_code=200)
async def get_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await service.get_task(task_id)


@router.patch("/{task_id}", response_model=TaskResponse, status_code=200)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await service.update_task(task_id, data)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
) -> None:
    await service.delete_task(task_id)
