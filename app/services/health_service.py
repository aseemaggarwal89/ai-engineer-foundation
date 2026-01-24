from app.domain.exceptions import ServiceError
from app.repositories.health_repository import HealthRepository


class HealthService:
    def __init__(self, repository: HealthRepository):
        self._repository = repository

    async def check(self) -> str:
        try:
            return await self._repository.fetch_status()
        except Exception as exc:
            # Translate low-level error into domain error
            raise ServiceError("Health check failed") from exc