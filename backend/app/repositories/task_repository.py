from __future__ import annotations

from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.common import TaskPriority, TaskStatus


class TaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, task: Task) -> Task:
        self._db.add(task)
        await self._db.commit()
        await self._db.refresh(task)
        return task

    async def find_by_id(self, task_id: str) -> Task | None:
        result = await self._db.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        keyword: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_before: date | None = None,
        due_after: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Task], int]:
        conditions = []
        if keyword:
            conditions.append(Task.title.ilike(f"%{keyword}%"))
        if status:
            conditions.append(Task.status == status.value)
        if priority:
            conditions.append(Task.priority == priority.value)
        if due_before:
            conditions.append(Task.due_date <= due_before)
        if due_after:
            conditions.append(Task.due_date >= due_after)

        where_clause = and_(*conditions) if conditions else True

        total_result = await self._db.execute(
            select(func.count()).select_from(Task).where(where_clause)
        )
        total: int = total_result.scalar_one()

        rows = await self._db.execute(
            select(Task)
            .where(where_clause)
            .order_by(Task.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows.scalars().all()), total

    async def search_by_title(
        self,
        keyword: str,
        due_date: date | None = None,
        limit: int = 5,
    ) -> list[Task]:
        """Case-insensitive title match with optional due-date narrowing.

        When due_date is supplied the query filters to tasks on that exact date,
        so 'dentist appointment tomorrow' never matches 'dentist appointment next week'.
        """
        conditions = [Task.title.ilike(f"%{keyword}%")]
        if due_date is not None:
            conditions.append(Task.due_date == due_date)

        result = await self._db.execute(
            select(Task)
            .where(and_(*conditions))
            .order_by(Task.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def save(self, task: Task) -> Task:
        await self._db.commit()
        await self._db.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self._db.delete(task)
        await self._db.commit()
