import logging
from app.application.ai.core.ai_reliability_pipeline import AIReliabilityPipeline
from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_inference_port import AIInferencePort
from app.application.ai.domain.ai_model_port import AIModelPort
from app.core.model_registry import ModelRegistry
from app.domain.exceptions.exceptions import (
    AIProviderError,
    ResponseValidationError,
    ServiceError,
)

logger = logging.getLogger(__name__)


class InferenceRouter(AIInferencePort):

    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    async def generate(
        self,
        *,
        capability: AICapability,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        primary = self.registry.get_primary(capability)
        fallback = self.registry.get_fallback(capability)

        # ---------------- PRIMARY ----------------
        try:
            logger.info("ai_router_primary_attempt")

            return await primary.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        except AIProviderError as exc:
            logger.warning(
                "ai_router_primary_provider_failed",
                exc_info=exc,
            )

        # ---------------- FALLBACK ----------------
        logger.info("ai_router_fallback_attempt")

        try:
            return await fallback.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        except AIProviderError as exc:
            logger.exception("ai_router_total_provider_failure")
            raise ServiceError("All AI providers failed") from exc
