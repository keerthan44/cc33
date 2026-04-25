import asyncio
import logging
from datetime import date

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.common import IntentType
from app.schemas.voice_schema import ExtractedIntent, IntentAction

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an intent extraction engine for a voice note-taking app. "
    "Today is {today}. Resolve ALL relative dates (e.g. 'tomorrow', 'next Friday', "
    "'three years from now') to absolute YYYY-MM-DD dates. "
    "The user may express MULTIPLE intents in a single utterance. "
    "Extract ALL intents and put each distinct intent into its own IntentAction in the actions array. "
    "Each IntentAction has an intent field: CREATE_TASK, UPDATE_TASK_STATUS, QUERY_TASKS, or GENERAL_NOTE. "
    "For CREATE_TASK: extract EVERY distinct task the user mentions into the tasks array — "
    "even if they mention two, three, or more things to do, each becomes its own TaskIntent. "
    "Never merge multiple actions into one task. "
    "For UPDATE_TASK_STATUS: use this intent for ANY modification to an existing task — "
    "changing its status (mark done, cancel, start) OR rescheduling/postponing its due date. "
    "Set task_identifier to the keyword that names the task (e.g. 'math homework', 'dentist'). "
    "Set new_status if the user is changing the status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED). "
    "Set new_due_date if the user is rescheduling or postponing (e.g. 'postpone to next month', "
    "'move to three years from now'). "
    "If the user also mentions a date to identify WHICH task they mean "
    "(e.g. 'the dentist appointment that was due today'), resolve that date and put it in task_due_date — "
    "this disambiguates between tasks with similar names; it is NOT the new due date. "
    "If the task might not exist yet, still use UPDATE_TASK_STATUS — the backend will create it. "
    "For QUERY_TASKS: populate the filters object with any combination of: "
    "keyword (partial title text), status, priority, due_before, due_after. "
    "If the user asks about multiple statuses separately (e.g. 'pending tasks' and 'completed tasks'), "
    "create a separate QUERY_TASKS IntentAction for each. "
    "For other intents the tasks array should be empty. "
    "Return null for optional fields not mentioned. "
    "Always return at least one IntentAction in the actions array."
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
        return ExtractedIntent(actions=[IntentAction(intent=IntentType.GENERAL_NOTE)])
