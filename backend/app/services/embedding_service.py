import asyncio
import logging

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

    @staticmethod
    def embed_text(title: str, description: str | None) -> str:
        return title if not description else f"{title}. {description}"

    def _embed_sync(self, text: str) -> list[float]:
        response = self._client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    async def embed(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embed_sync, text)
