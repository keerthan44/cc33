from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # noqa: F401 (selectinload still used for Note.tasks)

from app.models.note import Note


class NoteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_query(self):
        return select(Note).options(
            selectinload(Note.tasks),
        )

    async def create(self, note: Note) -> Note:
        self._db.add(note)
        await self._db.commit()
        result = await self._db.execute(
            self._base_query().where(Note.id == note.id)
        )
        return result.scalar_one()

    async def find_by_id(self, note_id: str) -> Note | None:
        result = await self._db.execute(
            self._base_query().where(Note.id == note_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        source: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Note], int]:
        conditions = []
        if source:
            conditions.append(Note.source == source)
        if date_from:
            conditions.append(func.date(Note.created_at) >= date_from)
        if date_to:
            conditions.append(func.date(Note.created_at) <= date_to)

        where_clause = and_(*conditions) if conditions else True

        total_result = await self._db.execute(
            select(func.count()).select_from(Note).where(where_clause)
        )
        total: int = total_result.scalar_one()

        rows = await self._db.execute(
            self._base_query()
            .where(where_clause)
            .order_by(Note.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows.scalars().all()), total
