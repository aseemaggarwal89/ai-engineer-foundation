from abc import ABC, abstractmethod
from typing import Optional


class AIResponseCachePort(ABC):

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> None:
        ...
    
    @abstractmethod
    def build_key(self, *,
                  capability: str,
                  prompt: str,
                  model: str,
                  temperature: float,
                  max_tokens: int) -> str:
        pass
