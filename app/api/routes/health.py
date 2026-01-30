import logging
from fastapi import APIRouter, Depends, Request

from app.db.models.health import HealthResponse
from app.domain.entities.user import User
from app.security.dependencies import get_current_user
from app.dependencies.use_cases import (
    get_check_health_status_use_case,
    get_liveness_usecase,
    get_readiness_usecase,
    get_deep_health_usecase,
)
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Public routes (no authentication)
# ---------------------------------------------------------------------

public_router = APIRouter(prefix="/health", tags=["health"])


@public_router.get("/")
async def root():
    """
    Public root endpoint.
    Used for basic service availability checks.
    """
    return {"message": "FastAPI service is running"}


@public_router.get("/live")
async def liveness(usecase=Depends(get_liveness_usecase)):
    logger.debug("Liveness endpoint hit")
    return await usecase.execute()


@public_router.get("/ready")
async def readiness(usecase=Depends(get_readiness_usecase)):
    logger.info("Readiness endpoint hit")
    return await usecase.execute()


@public_router.get("/deep")
async def deep_health(usecase=Depends(get_deep_health_usecase)):
    logger.info("Deep health endpoint hit")
    return await usecase.execute()

# ---------------------------------------------------------------------
# Protected routes (authentication required)
# ---------------------------------------------------------------------

protected_router = APIRouter(
    dependencies=[Depends(get_current_user)],  # 🔐 security guard
)


@protected_router.get(
    "/health",
    response_model=HealthResponse,
)
@limiter.limit("30/minute")
async def health_check(
    request: Request,  # ✅ REQUIRED for SlowAPI
    use_case=Depends(get_check_health_status_use_case),
    user: User = Depends(get_current_user),
) -> HealthResponse:
    """
    Health check endpoint.

    - Requires authentication
    - Uses dependency-injected health service
    - Receives resolved user from security guard
    """
    logger.debug("Health check endpoint called")

    status = await use_case.execute()

    return HealthResponse(
        status=f"{status} (user={user.email})"
    )
