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
    "Today is {today}. Resolve all relative dates (e.g. 'tomorrow', 'next Friday') "
    "to absolute YYYY-MM-DD dates. "
    "Classify the overall intent as one of: CREATE_TASK, UPDATE_TASK_STATUS, QUERY_TASKS, GENERAL_NOTE. "
    "For CREATE_TASK: extract EVERY distinct task the user mentions into the tasks array — "
    "even if they mention two, three, or more things to do, each becomes its own TaskIntent. "
    "Never merge multiple actions into one task. "
    "For UPDATE_TASK_STATUS: set task_identifier to the keyword that names the task. "
    "If the user also mentions a date to identify WHICH task they mean "
    "(e.g. 'the dentist appointment tomorrow'), resolve that date and put it in task_due_date — "
    "this is used to disambiguate between tasks with similar names, not to change the due date. "
    "For QUERY_TASKS: populate the filters object with any combination of: "
    "keyword (partial title text — e.g. 'dentist', 'PR', 'meeting'), "
    "status, priority, due_before, due_after. "
    "Use keyword when the user names or describes a specific task without knowing its exact title. "
    "The keyword drives a partial-text search so the DB returns the closest matching rows. "
    "For other intents the tasks array should be empty. "
    "Return null for optional fields not mentioned."
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
