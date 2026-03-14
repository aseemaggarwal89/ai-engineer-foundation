import logging

from fastapi.exceptions import ResponseValidationError
import json

from app.application.ai.core.ai_reliability_pipeline import AIReliabilityPipeline
from app.application.ai.core.bullet_parser import BulletParser
from app.application.ai.domain.ai_cache_port import AIResponseCachePort
from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_inference_port import AIInferencePort
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.application.ai.validator.prompt_evaluator import PromptEvaluator
from app.core.config import AISettings
from app.application.ai.domain.ai_model_port import AIModelPort

logger = logging.getLogger(__name__)


class SummaryService:

    def __init__(
        self,
        *,
        prompt: SummaryPrompt,
        inference: AIInferencePort,
        cache: AIResponseCachePort,
        settings: AISettings,
        reliability_pipeline: AIReliabilityPipeline,
        threshold: float = 0.6,
    ):
        self.inference = inference
        self.prompt = prompt
        self.cache = cache
        self.settings = settings
        self.pipeline = reliability_pipeline
        self.threshold = threshold

    async def summarize(self, text: str) -> list[str]:
        # ⭐ Build final LLM prompt first
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
        prompt_text = self.prompt.build(text)
        
        raw_output = await self.inference.generate(
            capability=AICapability.SUMMARIZATION,
            prompt=prompt_text,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )
        logger.info("validation_success", extra={"capability": "summarization", "raw_output": raw_output})

        bullets, score = self.pipeline.run(raw_output)
        if score < 0.6:
            raise ResponseValidationError("Low quality AI output")

        # ⭐ store result
        await self.cache.set(cache_key, json.dumps(bullets), ttl=3600)
        # # observability
        # self.evaluator.evaluate(
        #     prompt_version=self.prompt.VERSION,
        #     output=raw_output,
        # )
        
        return bullets