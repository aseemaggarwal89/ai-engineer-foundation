import pytest

from app.application.ai.core.container import ServiceContainer
from app.application.ai.domain.ai_provider import AIProvider
from app.application.ai.domain.model_registry import ModelRegistrySettings, ModelRoute
from app.core.config import AISettings, Settings


def make_settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///./test.db",
        jwt_secret_key="test-secret",
        ai=AISettings(
            provider=AIProvider.OPENAI,
            openai_api_key="sk-test",
            model_registry=ModelRegistrySettings(
                summarization=ModelRoute(primary=AIProvider.OPENAI),
            ),
        ),
    )


@pytest.mark.asyncio
async def test_ai_container_closes_reusable_async_clients_on_shutdown():
    container = ServiceContainer(make_settings())

    assert container.ollama_client.is_closed is False
    assert container.openai_client.is_closed() is False

    await container.shutdown()

    assert container.ollama_client.is_closed is True
    assert container.openai_client.is_closed() is True
