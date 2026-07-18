import logging
from typing import Dict
from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_model_port import AIModelPort
from app.application.ai.domain.ai_provider import AIProvider
from app.application.ai.domain.model_registry import ModelRoute
from app.core.config import AISettings
from app.domain.exceptions.exceptions import ServiceError

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Maps AI capabilities to provider adapters.

    Settings define the route, for example summarization -> Ollama primary
    with OpenAI fallback. The container registers concrete adapters, and the
    inference router asks this registry for the correct adapter at runtime.
    """

    def __init__(self, aisettings: AISettings):

        self.aisettings = aisettings
        self._adapters: Dict[AIProvider, AIModelPort] = {}
        self._mapping: Dict[AICapability, ModelRoute] = {}

    async def load(self):
        """Load capability routes from validated application settings."""
        config = self.aisettings.model_registry
        if not config:
            logger.warning("model_registry_not_configured")
            return

        self._mapping[AICapability.SUMMARIZATION] = config.summarization
        if config.chat:
            self._mapping[AICapability.CHAT] = config.chat
            
    def register_adapter(self, name: AIProvider, adapter: AIModelPort):
        """Register one concrete provider implementation behind its enum key."""
        self._adapters[name] = adapter

    def get_primary(self, capability: AICapability) -> AIModelPort:
        """Return the configured primary provider for a capability."""
        route = self._get_route(capability)

        return self._adapters[route.primary]

    def get_fallback(self, capability: AICapability) -> AIModelPort | None:
        """Return the optional fallback provider for a capability."""
        route = self._get_route(capability)

        if route.fallback:
            return self._adapters[route.fallback]

        return None

    def _get_route(self, capability: AICapability) -> ModelRoute:
        # Fail with domain errors instead of leaking KeyError into HTTP handlers.
        route = self._mapping.get(capability)

        if not route:
            raise ServiceError(f"No AI model route configured for {capability.value}")

        if route.primary not in self._adapters:
            raise ServiceError(f"No AI adapter registered for {route.primary.value}")

        if route.fallback and route.fallback not in self._adapters:
            raise ServiceError(f"No AI fallback adapter registered for {route.fallback.value}")

        return route

    async def close(self):
        self._adapters.clear()
