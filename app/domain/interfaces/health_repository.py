from abc import ABC, abstractmethod


class HealthRepository(ABC):
    @abstractmethod
    async def fetch_status(self) -> str:
        pass