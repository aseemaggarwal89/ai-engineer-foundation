from app.application.ai.validator.request.ai_guardrails import AIGuardrails
from app.application.ai.services.summary_service import SummaryService
from app.application.ai.validator.request.ai_safety import AISafetyFilter
from app.core.config import AISettings
from app.core.timeout import timeout_from_self


class SummarizeTextUseCase:
    """
    Application boundary for summarization.

    Workflow:
    apply request-side safety checks -> validate and normalize permitted input
    -> delegate prompt, cache, inference, and response processing to
    SummaryService. This keeps HTTP and provider details out of the use case.
    """

    def __init__(
        self,
        guardrails: AIGuardrails,
        safety: AISafetyFilter,
        summary_service: SummaryService,
        ai_settings: AISettings,
    ):
        self.guardrails = guardrails
        self.safety = safety
        self.summary_service = summary_service
        self.timeout_seconds = ai_settings.timeout_seconds

    @timeout_from_self
    async def execute(self, text: str) -> list[str]:
        # Request-side protections run before prompt construction or provider calls.
        self.safety.check(text)
        text = self.guardrails.validate_prompt(text)

        return await self.summary_service.summarize(text)
