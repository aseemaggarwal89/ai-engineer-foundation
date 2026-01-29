import logging
from app.domain.interfaces.health_repository import HealthRepository
from app.domain.exceptions.exceptions import ServiceError

logger = logging.getLogger(__name__)


class CheckHealthStatusUseCase:
    """
    Application-level use case for system health.
    """

    def __init__(self, health_repo: HealthRepository):
        self.health_repo = health_repo

    async def execute(self) -> str:
        # 1️⃣ Health check attempt (low noise)
        logger.debug(
            "Health check started",
            extra={
                "event": "health_check_attempt",
            },
        )

        try:
            status = await self.health_repo.fetch_status()

            # 2️⃣ Health check success (low noise)
            logger.debug(
                "Health check successful",
                extra={
                    "event": "health_check_success",
                    "status": status,
                },
            )

            return status

        except Exception as exc:
            # 3️⃣ Health check failure (high signal)
            logger.error(
                "Health check failed",
                extra={
                    "event": "health_check_failed",
                    "error_type": type(exc).__name__,
                },
            )
            raise ServiceError("Health check failed") from exc
