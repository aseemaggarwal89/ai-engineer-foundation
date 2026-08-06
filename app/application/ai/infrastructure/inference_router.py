import logging
from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_inference_port import AIInferencePort
from app.core.model_registry import ModelRegistry
from app.domain.exceptions.exceptions import (
    AIProviderError,
    ServiceError,
)

logger = logging.getLogger(__name__)


class InferenceRouter(AIInferencePort):
    """
    Capability-aware inference gateway.

    Callers request an AI capability, not a vendor. The router asks
    ModelRegistry for the primary provider and falls back only when the primary
    raises AIProviderError, which means provider adapters must normalize
    transport/vendor failures into that domain exception.
    """

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

        # Try the cheapest/preferred provider first.
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
                extra={
                    "provider": exc.provider,
                    "model": exc.model,
                    "category": exc.category.value,
                    "fallback_eligible": exc.fallback_eligible,
                },
            )
            if not exc.fallback_eligible:
                raise ServiceError("Primary AI provider failed with a non-fallback error") from exc

        # Missing fallback is a configuration decision, not an AttributeError.
        if fallback is None:
            logger.exception("ai_router_no_fallback_configured")
            raise ServiceError("Primary AI provider failed and no fallback is configured")

        # Fallback keeps the application available when the primary provider is
        # rate limited, down, or timing out.
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
