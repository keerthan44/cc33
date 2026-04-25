import pytest
from unittest.mock import patch

from app.schemas.common import IntentType
from app.schemas.voice_schema import ExtractedIntent, IntentAction
from app.services.intent_service import IntentService


class TestIntentServiceFallback:
    @pytest.mark.asyncio
    async def test_fallback_returns_general_note_when_all_retries_fail(self):
        service = IntentService()
        with patch.object(service, "_invoke", side_effect=Exception("LLM error")):
            result = await service.extract_intent("test", max_retries=0)
        assert isinstance(result, ExtractedIntent)
        assert result.actions[0].intent == IntentType.GENERAL_NOTE

    @pytest.mark.asyncio
    async def test_returns_result_on_first_success(self):
        service = IntentService()
        expected = ExtractedIntent(actions=[IntentAction(intent=IntentType.GENERAL_NOTE)])
        with patch.object(service, "_invoke", return_value=expected):
            result = await service.extract_intent("test")
        assert result == expected

    @pytest.mark.asyncio
    async def test_retries_on_transient_failure_then_succeeds(self):
        service = IntentService()
        success = ExtractedIntent(actions=[IntentAction(intent=IntentType.CREATE_TASK)])
        call_count = 0

        def flaky_invoke(*_):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("transient")
            return success

        with patch.object(service, "_invoke", side_effect=flaky_invoke):
            result = await service.extract_intent("test", max_retries=2)
        assert result.actions[0].intent == IntentType.CREATE_TASK
        assert call_count == 2
