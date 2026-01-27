# app/domain/use_cases/system/check_health_status.py

from app.domain.interfaces.health_repository import HealthRepository
from app.domain.exceptions.exceptions import ServiceError


class CheckHealthStatusUseCase:
    """
    Application-level use case for system health.

    Intentionally simple today.
    Designed for future expansion:
    - dependency checks
    - external service probes
    - readiness vs liveness
    """

    def __init__(self, health_repo: HealthRepository):
        self.health_repo = health_repo

    async def execute(self) -> str:
        try:
            return await self.health_repo.fetch_status()
        except Exception as exc:
            raise ServiceError("Health check failed") from exc
