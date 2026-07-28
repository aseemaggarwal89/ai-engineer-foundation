import asyncio

import pytest

from app.application.ai.usecases.summarize_text import SummarizeTextUseCase
from app.domain.exceptions.exceptions import ServiceError


class PassThroughGuardrails:
    def validate_prompt(self, text: str) -> str:
        return text


class PassThroughSafety:
    def check(self, text: str) -> None:
        return None


class SlowSummaryService:
    async def summarize(self, text: str) -> list[str]:
        await asyncio.sleep(0.05)
        return ["too late"]


class TimeoutSettings:
    timeout_seconds = 0.01


@pytest.mark.asyncio
async def test_summarize_use_case_translates_timeout_to_service_error():
    use_case = SummarizeTextUseCase(
        guardrails=PassThroughGuardrails(),
        safety=PassThroughSafety(),
        summary_service=SlowSummaryService(),
        ai_settings=TimeoutSettings(),
    )

    with pytest.raises(ServiceError) as exc_info:
        await use_case.execute("slow text")

    assert "execute timed out" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, asyncio.TimeoutError)
