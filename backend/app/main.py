from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    health_controller,
    note_controller,
    task_controller,
    voice_controller,
)
from app.core.config import settings
from app.core.database import init_db
from app.core.dependencies import init_services


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    init_services()
    yield


app = FastAPI(title="Voice Note Taker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_controller.router, prefix="/api")
app.include_router(task_controller.router, prefix="/api")
app.include_router(note_controller.router, prefix="/api")
app.include_router(voice_controller.router, prefix="/api")
