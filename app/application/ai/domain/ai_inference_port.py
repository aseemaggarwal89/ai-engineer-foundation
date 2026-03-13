from abc import ABC, abstractmethod
from app.application.ai.domain.ai_capability import AICapability


class AIInferencePort(ABC):
    @abstractmethod
    async def generate(
        self,
        *,
        capability: AICapability,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        pass