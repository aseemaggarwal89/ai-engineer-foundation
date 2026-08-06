import json

import pytest

from app.application.ai.core.pipeline_registry import PipelineRegistry
from app.application.ai.domain.ai_cache_port import AIResponseCachePort
from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_provider import AIProvider
from app.application.ai.domain.ai_inference_port import AIInferencePort
from app.application.ai.domain.ai_pipeline_port import AIResponsePipeline
from app.application.ai.domain.model_registry import ModelRegistrySettings, ModelRoute
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.application.ai.services.summary_service import SummaryService
from app.core.config import AISettings
from app.domain.exceptions.exceptions import ResponseValidationError


class FakePrompt(SummaryPrompt):
    VERSION = "test-v1"

    def build(self, text: str) -> str:
        return f"Summarize: {text}"


class FakeCache(AIResponseCachePort):
    def __init__(self, cached_value: str | None = None):
        self.cached_value = cached_value
        self.set_calls: list[tuple[str, str, int]] = []
        self.key_parts: dict[str, object] = {}
        self.get_key: str | None = None

    def build_key(self, **kwargs) -> str:
        self.key_parts = dict(kwargs)
        return "summary-cache-key"

    async def get(self, key: str) -> str | None:
        self.get_key = key
        return self.cached_value

    async def set(self, key: str, value: str, ttl: int) -> None:
        self.set_calls.append((key, value, ttl))


class FakeInference(AIInferencePort):
    def __init__(self):
        self.called = False
        self.kwargs: dict[str, object] = {}

    async def generate(self, **kwargs) -> str:
        self.called = True
        self.kwargs = dict(kwargs)
        return "- Fresh bullet"


class FakePipeline(AIResponsePipeline):
    def __init__(self, score: float = 1.0):
        self.score = score

    def run(self, raw_response: str) -> tuple[list[str], float]:
        self.raw_response = raw_response
        return ["Fresh bullet"], self.score


class FakePipelineRegistry(PipelineRegistry):
    def __init__(self, pipeline: FakePipeline | None = None):
        self.pipeline = pipeline or FakePipeline()

    def get(self, capability: AICapability) -> FakePipeline:
        self.capability = capability
        return self.pipeline


def make_service(
    cache: FakeCache,
    inference: FakeInference,
    pipeline_registry: FakePipelineRegistry | None = None,
    settings: AISettings | None = None,
) -> SummaryService:
    return SummaryService(
        prompt=FakePrompt(),
        inference=inference,
        cache=cache,
        settings=settings or AISettings(
            model_name="tinyllama",
            temperature=0.6,
            max_tokens=512,
        ),
        pipeline_registry=pipeline_registry or FakePipelineRegistry(),
    )


@pytest.mark.asyncio
async def test_summary_service_returns_cached_response_without_provider_call():
    cache = FakeCache(
        cached_value=json.dumps(
            {
                "schema_version": SummaryService.CACHE_SCHEMA_VERSION,
                "bullets": ["Cached bullet"],
            }
        )
    )
    inference = FakeInference()
    service = make_service(cache, inference)

    result = await service.summarize("cached text")

    assert result == ["Cached bullet"]
    assert cache.get_key == "summary-cache-key"
    assert inference.called is False
    assert cache.set_calls == []


@pytest.mark.asyncio
async def test_summary_service_populates_cache_after_cache_miss():
    cache = FakeCache()
    inference = FakeInference()
    service = make_service(cache, inference)

    result = await service.summarize("fresh text")

    assert result == ["Fresh bullet"]
    assert inference.called is True
    assert inference.kwargs["capability"] == AICapability.SUMMARIZATION
    assert cache.key_parts["prompt"].startswith("test-v1|")
    assert cache.key_parts["namespace"] == "local"
    assert cache.key_parts["schema_version"] == SummaryService.CACHE_SCHEMA_VERSION
    assert cache.key_parts["model_identity"] == (
        "primary=ollama:tinyllama;fallback=none"
    )
    assert cache.set_calls == [
        (
            "summary-cache-key",
            json.dumps(
                {
                    "schema_version": SummaryService.CACHE_SCHEMA_VERSION,
                    "bullets": ["Fresh bullet"],
                }
            ),
            3600,
        )
    ]


@pytest.mark.asyncio
async def test_summary_service_rejects_low_quality_output_without_caching():
    cache = FakeCache()
    inference = FakeInference()
    pipeline_registry = FakePipelineRegistry(FakePipeline(score=0.5))
    service = make_service(cache, inference, pipeline_registry)

    with pytest.raises(
        ResponseValidationError,
        match="AI output did not satisfy the summary response contract",
    ):
        await service.summarize("fresh text")

    assert inference.called is True
    assert cache.set_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cached_value",
    [
        "not json",
        json.dumps(["old raw list"]),
        json.dumps({"schema_version": 999, "bullets": ["old schema"]}),
        json.dumps({"schema_version": SummaryService.CACHE_SCHEMA_VERSION}),
        json.dumps(
            {
                "schema_version": SummaryService.CACHE_SCHEMA_VERSION,
                "bullets": [],
            }
        ),
        json.dumps(
            {
                "schema_version": SummaryService.CACHE_SCHEMA_VERSION,
                "bullets": [""],
            }
        ),
    ],
)
async def test_summary_service_treats_invalid_cached_value_as_cache_miss(cached_value):
    cache = FakeCache(cached_value=cached_value)
    inference = FakeInference()
    service = make_service(cache, inference)

    result = await service.summarize("fresh text")

    assert result == ["Fresh bullet"]
    assert inference.called is True
    assert len(cache.set_calls) == 1


@pytest.mark.asyncio
async def test_summary_service_cache_identity_includes_configured_fallback_route():
    cache = FakeCache()
    inference = FakeInference()
    settings = AISettings(
        openai_api_key="sk-test",
        model_name="tinyllama",
        temperature=0.6,
        max_tokens=512,
        model_registry=ModelRegistrySettings(
            summarization=ModelRoute(
                primary=AIProvider.OLLAMA,
                fallback=AIProvider.OPENAI,
            )
        ),
    )
    service = make_service(cache, inference, settings=settings)

    await service.summarize("fresh text")

    assert cache.key_parts["model_identity"] == (
        "primary=ollama:tinyllama;fallback=openai:gpt-4.1-mini"
    )
