import logging
from app.application.ai.core.ai_reliability_pipeline import AIReliabilityPipeline
from app.application.ai.domain.ai_model_port import AIModelPort
from app.domain.exceptions.exceptions import AIProviderError, ResponseValidationError, ServiceError

logger = logging.getLogger(__name__)


class FallbackModelRouter(AIModelPort):

    def __init__(
        self,
        primary: AIModelPort,
        fallback: AIModelPort,
        reliability_pipeline: AIReliabilityPipeline,
        threshold: float = 0.6,
    ):
        self.primary = primary
        self.fallback = fallback
        self.pipeline = reliability_pipeline
        self.threshold = threshold

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:

        score = None  # 🔥 prevents referenced-before-assignment bug

        # ---------------- PRIMARY ----------------
        try:
            logger.info("ai_router_primary_attempt")

            response = await self.primary.generate(
                prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        except AIProviderError as exc:
            logger.warning(
                "ai_router_primary_provider_failed",
                exc_info=exc,
            )

        else:
            # 🔥 DO NOT wrap pipeline in try
            # If this crashes → YOUR SYSTEM is broken
            validated, score = self.pipeline.run(response)

            if score >= self.threshold:
                return validated

            logger.warning(
                "ai_router_low_score_fallback",
                extra={"score": score},
            )

        # ---------------- FALLBACK ----------------
        logger.info("ai_router_fallback_attempt")

        try:
            response = await self.fallback.generate(
                prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            validated, score = self.pipeline.run(response)

            if score < self.threshold:
                raise ResponseValidationError(
                    "Fallback model produced low-quality output"
                )

            return validated

        except AIProviderError as exc:
            logger.exception("ai_router_total_provider_failure")
            raise ServiceError("All AI providers failed") from exc