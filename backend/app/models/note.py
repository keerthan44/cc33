from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._utils import new_uuid
from app.models.task import Task


note_tasks = Table(
    "note_tasks",
    Base.metadata,
    Column("note_id", String, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("task_id", String, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    raw_transcript: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="voice")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actions_json: Mapped[str | None] = mapped_column(String, nullable=True)

    tasks: Mapped[list[Task]] = relationship("Task", secondary=note_tasks)

    __table_args__ = (
        Index("ix_notes_source", "source"),
        Index("ix_notes_created_at", "created_at"),
    )
