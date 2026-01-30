import logging
from app.core.tracer import traced
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


class LivenessCheckUseCase:
    """
    Verifies process is alive.
    No dependency checks.
    """

    async def execute(self) -> str:
        logger.debug("Liveness check executed")
        return {"status": "alive"}


class ReadinessCheckUseCase:
    """
    Verifies system is ready to serve traffic.
    Checks critical dependencies.
    """

    def __init__(self, repo: HealthRepository):
        self.repo = repo

    @traced("usecase.check_health")
    async def execute(self) -> str:
        logger.info("Readiness check started")

        try:
            await self.repo.fetch_status()
            logger.info("Readiness check passed")
            return {"status": "ready"}

        except Exception as exc:
            logger.error("Readiness check failed", exc_info=True)
            raise ServiceError("Service not ready") from exc


class DeepHealthCheckUseCase:
    """
    Full dependency verification.
    """

    def __init__(self, repo: HealthRepository):
        self.repo = repo

    async def execute(self) -> dict:
        logger.info("Deep health check started")

        result = {}

        try:
            await self.repo.fetch_status()
            result["database"] = "ok"
        except Exception:
            result["database"] = "fail"

        # future: model registry, vector DB, etc.
        result["service"] = "ok"

        logger.info("Deep health check completed", extra={"health": result})
        return result