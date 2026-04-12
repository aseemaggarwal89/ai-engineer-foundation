from abc import ABC, abstractmethod
from typing import Any


class AIResponsePipeline(ABC):

    @abstractmethod
    def run(self, raw_response: str) -> tuple[Any, float]:
        ...