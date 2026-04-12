from app.application.ai.core.summarization_pipeline import SummarizationPipeline
from app.application.ai.validator.request.ai_guardrails import AIGuardrails
from app.application.ai.services.summary_service import SummaryService
from app.application.ai.validator.request.ai_safety import AISafetyFilter
from app.application.ai.validator.response.hallucination_guard import HallucinationGuard
from app.application.ai.validator.response.response_scorer import AIResponseScorer
from app.application.ai.validator.response.response_validator import AIResponseValidator
from app.core.config import AISettings
from app.core.timeout import timeout_from_self


class SummarizeTextUseCase:

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
        # 🔥 Layer 7 protections
        self.safety.check(text)
        text = self.guardrails.validate_prompt(text)

        bullets = await self.summary_service.summarize(text)

        return bullets