from abc import ABC, abstractmethod


class AIModelPort(ABC):

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float,
        max_tokens: int
    ) -> str:
        pass
