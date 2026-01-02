from typing import Protocol


class HealthServiceProtocol(Protocol):
    async def check(self) -> str:
        ...