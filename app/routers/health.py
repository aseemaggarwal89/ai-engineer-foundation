import logging
from fastapi import APIRouter, Depends

from app.db.models.health import HealthResponse
from app.db.models.user import User
from app.services.health_protocol import HealthServiceProtocol
from app.dependencies.deps import (
    health_service,
    get_current_user,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Public routes (no authentication)
# ---------------------------------------------------------------------

public_router = APIRouter()


@public_router.get("/")
async def root():
    """
    Public root endpoint.
    Used for basic service availability checks.
    """
    return {"message": "FastAPI service is running"}


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
async def health_check(
    service: HealthServiceProtocol = Depends(health_service),
    current_user: User = Depends(get_current_user),
) -> HealthResponse:
    """
    Health check endpoint.

    - Requires authentication
    - Uses dependency-injected health service
    - Receives resolved user from security guard
    """
    logger.debug("Health check endpoint called")

    status = await service.check()

    return HealthResponse(
        status=f"{status} (user={current_user.id})"
    )
