import pytest

from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.infrastructure.inference_router import InferenceRouter
from app.domain.exceptions.exceptions import (
    AIProviderError,
    ProviderErrorCategory,
    ServiceError,
)


class FakeProvider:
    def __init__(self, response: str | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.called = False

    async def generate(self, **kwargs) -> str:
        self.called = True
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response or ""


class FakeRegistry:
    def __init__(self, primary: FakeProvider, fallback: FakeProvider | None = None):
        self.primary = primary
        self.fallback = fallback

    def get_primary(self, capability: AICapability) -> FakeProvider:
        self.capability = capability
        return self.primary

    def get_fallback(self, capability: AICapability) -> FakeProvider | None:
        self.capability = capability
        return self.fallback


@pytest.mark.asyncio
async def test_inference_router_uses_fallback_when_primary_provider_fails():
    primary = FakeProvider(error=AIProviderError("primary failed"))
    fallback = FakeProvider(response="fallback response")
    router = InferenceRouter(FakeRegistry(primary, fallback))

    result = await router.generate(
        capability=AICapability.SUMMARIZATION,
        prompt="prompt",
        temperature=0.6,
        max_tokens=128,
    )

    assert result == "fallback response"
    assert primary.called is True
    assert fallback.called is True


@pytest.mark.asyncio
async def test_inference_router_raises_service_error_without_fallback():
    primary = FakeProvider(error=AIProviderError("primary failed"))
    router = InferenceRouter(FakeRegistry(primary))

    with pytest.raises(ServiceError):
        await router.generate(
            capability=AICapability.SUMMARIZATION,
            prompt="prompt",
            temperature=0.6,
            max_tokens=128,
        )


@pytest.mark.asyncio
async def test_inference_router_does_not_fallback_for_non_fallback_provider_error():
    primary = FakeProvider(
        error=AIProviderError(
            "auth failed",
            category=ProviderErrorCategory.AUTHENTICATION,
        )
    )
    fallback = FakeProvider(response="fallback response")
    router = InferenceRouter(FakeRegistry(primary, fallback))

    with pytest.raises(ServiceError):
        await router.generate(
            capability=AICapability.SUMMARIZATION,
            prompt="prompt",
            temperature=0.6,
            max_tokens=128,
        )

    assert primary.called is True
    assert fallback.called is False
