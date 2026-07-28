import json
from types import SimpleNamespace

import pytest

from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.services.summary_service import SummaryService


class FakePrompt:
    def build(self, text: str) -> str:
        return f"Summarize: {text}"


class FakeCache:
    def __init__(self, cached_value: str | None = None):
        self.cached_value = cached_value
        self.set_calls = []

    def build_key(self, **kwargs) -> str:
        self.key_parts = kwargs
        return "summary-cache-key"

    async def get(self, key: str) -> str | None:
        self.get_key = key
        return self.cached_value

    async def set(self, key: str, value: str, ttl: int) -> None:
        self.set_calls.append((key, value, ttl))


class FakeInference:
    def __init__(self):
        self.called = False

    async def generate(self, **kwargs) -> str:
        self.called = True
        self.kwargs = kwargs
        return "- Fresh bullet"


class FakePipeline:
    def run(self, raw_response: str) -> tuple[list[str], float]:
        self.raw_response = raw_response
        return ["Fresh bullet"], 1.0


class FakePipelineRegistry:
    def __init__(self):
        self.pipeline = FakePipeline()

    def get(self, capability: AICapability) -> FakePipeline:
        self.capability = capability
        return self.pipeline


def make_service(cache: FakeCache, inference: FakeInference) -> SummaryService:
    return SummaryService(
        prompt=FakePrompt(),
        inference=inference,
        cache=cache,
        settings=SimpleNamespace(
            model_name="tinyllama",
            temperature=0.6,
            max_tokens=512,
        ),
        pipeline_registry=FakePipelineRegistry(),
    )


@pytest.mark.asyncio
async def test_summary_service_returns_cached_response_without_provider_call():
    cache = FakeCache(cached_value=json.dumps(["Cached bullet"]))
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
    assert cache.set_calls == [
        ("summary-cache-key", json.dumps(["Fresh bullet"]), 3600)
    ]
