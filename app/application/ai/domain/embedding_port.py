from abc import ABC, abstractmethod
from typing import List


class EmbeddingPort(ABC):

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        ...