import logging

import json
from json import JSONDecodeError

from app.application.ai.core.pipeline_registry import PipelineRegistry
from app.application.ai.domain.ai_cache_port import AIResponseCachePort
from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_inference_port import AIInferencePort
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.core.config import AISettings
from app.domain.exceptions.exceptions import ResponseValidationError, ServiceError

logger = logging.getLogger(__name__)


class SummaryService:
    CACHE_SCHEMA_VERSION = 1

    """
    Orchestrates the summarization workflow after input is considered safe.

    The service owns application-level AI flow:
    prompt build -> cache lookup -> inference -> response pipeline -> cache write.
    It depends on ports/registries so providers and cache backends can change
    without changing this workflow.
    """

    def __init__(
        self,
        *,
        prompt: SummaryPrompt,
        inference: AIInferencePort,
        cache: AIResponseCachePort,
        settings: AISettings,
        pipeline_registry: PipelineRegistry,
        threshold: float = 0.6,
    ):
        self.inference = inference
        self.prompt = prompt
        self.cache = cache
        self.settings = settings
        self.pipeline_registry = pipeline_registry
        self.threshold = threshold

    async def summarize(self, text: str) -> list[str]:
        # Prompt text is intentionally part of the cache key so prompt changes
        # naturally invalidate stale cached summaries. The explicit prompt
        # version protects the cache when the prompt contract changes.
        prompt_text = self.prompt.build(text)
        prompt_fingerprint = f"{self.prompt.VERSION}|{prompt_text}"
        model_identity = self._routing_policy_identity()

        cache_key = self.cache.build_key(
            namespace=self.settings.cache_namespace,
            capability=AICapability.SUMMARIZATION.value,
            prompt=prompt_fingerprint,
            model_identity=model_identity,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            schema_version=self.CACHE_SCHEMA_VERSION,
        )
        cached = await self.cache.get(cache_key)
        if cached:
            cached_bullets = self._load_cached_bullets(cached)
            if cached_bullets:
                logger.info("ai_cache_hit", extra={"capability": "summarization"})
                return cached_bullets
            logger.warning(
                "ai_cache_invalid",
                extra={"capability": "summarization"},
            )

        logger.info("ai_cache_miss", extra={"capability": "summarization"})

        # Provider selection and fallback live behind the inference port.
        raw_output = await self.inference.generate(
            capability=AICapability.SUMMARIZATION,
            prompt=prompt_text,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )
        logger.info(
            "ai_inference_response_received",
            extra={
                "capability": "summarization",
                "raw_output_chars": len(raw_output),
            },
        )

        # The model response is unvalidated until the registered reliability
        # pipeline parses, validates, guards, and scores it.
        pipeline = self.pipeline_registry.get(AICapability.SUMMARIZATION)
        bullets, score = pipeline.run(raw_output)

        if score < self.threshold:
            raise ResponseValidationError(
                "AI output did not satisfy the summary response contract"
            )

        # Cache only post-validated structured output, never raw provider text.
        await self.cache.set(
            cache_key,
            json.dumps(
                {
                    "schema_version": self.CACHE_SCHEMA_VERSION,
                    "bullets": bullets,
                }
            ),
            ttl=self.settings.cache_ttl_seconds,
        )

        return bullets

    def _routing_policy_identity(self) -> str:
        """
        Cache by configured routing policy, not by whichever provider wins a
        fallback attempt. This treats configured primary/fallback providers as
        interchangeable for this summarization capability.
        """
        route = (
            self.settings.model_registry.summarization
            if self.settings.model_registry
            else None
        )
        primary_provider = route.primary if route else self.settings.provider
        fallback_provider = route.fallback if route else None

        primary_model = primary_provider.get_model_name()
        fallback = "none"
        if fallback_provider:
            fallback = f"{fallback_provider.value}:{fallback_provider.get_model_name()}"

        if not primary_model:
            raise ServiceError("AI model is not configured")

        return f"primary={primary_provider.value}:{primary_model};fallback={fallback}"

    def _load_cached_bullets(self, cached: str) -> list[str] | None:
        try:
            payload = json.loads(cached)
        except (JSONDecodeError, TypeError):
            return None

        if not isinstance(payload, dict):
            return None

        if payload.get("schema_version") != self.CACHE_SCHEMA_VERSION:
            return None

        bullets = payload.get("bullets")
        if not isinstance(bullets, list) or not bullets:
            return None

        if not all(isinstance(bullet, str) and bullet.strip() for bullet in bullets):
            return None

        return bullets
