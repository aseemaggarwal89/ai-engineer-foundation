from app.application.ai.core.ai_reliability_pipeline import AIReliabilityPipeline
from app.application.ai.validator.request.ai_guardrails import AIGuardrails
from app.application.ai.services.summary_service import SummaryService
from app.application.ai.validator.request.ai_safety import AISafetyFilter
from app.application.ai.validator.response.hallucination_guard import HallucinationGuard
from app.application.ai.validator.response.response_scorer import AIResponseScorer
from app.application.ai.validator.response.response_validator import AIResponseValidator
from app.core.config import AISettings
from app.core.timeout import timeout, timeout_from_self
from app.domain.exceptions.exceptions import ResponseValidationError


class SummarizeTextUseCase:

    def __init__(
        self,
        guardrails: AIGuardrails,
        safety: AISafetyFilter,
        reliability_pipeline: AIReliabilityPipeline,
        summary_service: SummaryService,
        ai_settings: AISettings,
    ):
        self.guardrails = guardrails
        self.safety = safety
        self.reliability_pipeline = reliability_pipeline
        self.summary_service = summary_service
        self.timeout_seconds = ai_settings.timeout_seconds

    @timeout_from_self
    async def execute(self, text: str) -> list[str]:
        # 🔥 Layer 7 protections
        self.safety.check(text)
        self.guardrails.validate_prompt(text)
        try:
            bullets = await self.summary_service.summarize(text)

        except Exception:
            if not self.fallback_service:
                raise

        # Zero-trust boundary
        validatedResponse, score = self.reliability_pipeline.run(response=bullets)
        if score < 0.6:
            raise ResponseValidationError("Low confidence AI output")

        return validatedResponse
