import logging

import json

from app.application.ai.core.pipeline_registry import PipelineRegistry
from app.application.ai.domain.ai_cache_port import AIResponseCachePort
from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_inference_port import AIInferencePort
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.core.config import AISettings
from app.domain.exceptions.exceptions import ResponseValidationError

logger = logging.getLogger(__name__)


class SummaryService:
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
        # naturally invalidate stale cached summaries.
        prompt_text = self.prompt.build(text)

        cache_key = self.cache.build_key(
            capability=AICapability.SUMMARIZATION.value,
            prompt=prompt_text,
            model=self.settings.model_name,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info("ai_cache_hit", extra={"capability": "summarization"})
            return json.loads(cached)
        
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

        # The model response is untrusted until the registered reliability
        # pipeline parses, validates, guards, and scores it.
        pipeline = self.pipeline_registry.get(AICapability.SUMMARIZATION)
        bullets, score = pipeline.run(raw_output)
        
        if score < self.threshold:
            raise ResponseValidationError("Low quality AI output")

        # Cache only post-validated structured output, never raw provider text.
        await self.cache.set(cache_key, json.dumps(bullets), ttl=3600)
        
        return bullets
