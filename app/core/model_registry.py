import logging
from typing import Dict
from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_model_port import AIModelPort
from app.application.ai.domain.model_registry import ModelRoute
from app.core.config import AISettings

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Central place that maps AI capabilities to models.
    """

    def __init__(self, aisettings: AISettings):

        self.aisettings = aisettings
        self._adapters: Dict[str, AIModelPort] = {}
        self._mapping: Dict[AICapability, ModelRoute] = {}

    async def load(self):
        config = self.aisettings.model_registry
        if not config:
            logger.warning("model_registry_not_configured")
            return

        self._mapping[AICapability.SUMMARIZATION] = config.summarization
        if config.chat:
            self._mapping[AICapability.CHAT] = config.chat
            
    def register_adapter(self, name: str, adapter: AIModelPort):
        self._adapters[name] = adapter

    def get_primary(self, capability: AICapability) -> AIModelPort:

        route = self._mapping[capability]

        return self._adapters[route.primary]

    def get_fallback(self, capability: AICapability) -> AIModelPort:

        route = self._mapping[capability]

        if route.fallback:
            return self._adapters[route.fallback]

        return None

    async def close(self):
        self._adapters.clear()