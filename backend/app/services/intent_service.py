import asyncio
import logging
from datetime import date

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.common import IntentType
from app.schemas.voice_schema import ExtractedIntent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an intent extraction engine for a voice note-taking app. "
    "Extract intent from the transcript and return structured data. "
    "Today is {today}. Resolve all relative dates (e.g. 'tomorrow', 'next Friday') "
    "to absolute YYYY-MM-DD dates. "
    "Return null for any field not mentioned or inferable from the transcript."
)


class IntentService:
    def __init__(self) -> None:
        self._chain = None

    def _get_chain(self):
        if self._chain is None:
            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=0,
            )
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", _SYSTEM_PROMPT),
                    ("human", "{transcript}"),
                ]
            )
            self._chain = prompt | llm.with_structured_output(ExtractedIntent)
        return self._chain

    def _invoke(self, transcript: str) -> ExtractedIntent:
        return self._get_chain().invoke(
            {"transcript": transcript, "today": date.today().isoformat()}
        )

    async def extract_intent(
        self, transcript: str, max_retries: int = 2
    ) -> ExtractedIntent:
        for attempt in range(max_retries + 1):
            try:
                result = await asyncio.to_thread(self._invoke, transcript)
                return result
            except Exception as exc:
                logger.error(
                    "Intent extraction attempt %d/%d failed: %s",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )
        return ExtractedIntent(intent=IntentType.GENERAL_NOTE)
