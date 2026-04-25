from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent schema evolution (runs safely on every startup)
        await conn.execute(text(
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS actions_json TEXT"
        ))
        await conn.execute(text(
            "ALTER TABLE notes DROP COLUMN IF EXISTS task_id"
        ))
        # HNSW index for fast cosine similarity search on task embeddings
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_tasks_embedding_hnsw "
            "ON tasks USING hnsw (embedding vector_cosine_ops)"
        ))
        # Ensure note_tasks FK constraints use CASCADE
        await conn.execute(text("""
            DO $$
            BEGIN
                ALTER TABLE note_tasks DROP CONSTRAINT IF EXISTS note_tasks_task_id_fkey;
                ALTER TABLE note_tasks ADD CONSTRAINT note_tasks_task_id_fkey
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE;
                ALTER TABLE note_tasks DROP CONSTRAINT IF EXISTS note_tasks_note_id_fkey;
                ALTER TABLE note_tasks ADD CONSTRAINT note_tasks_note_id_fkey
                    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE;
            END$$;
        """))
