import logging
from fastapi import APIRouter, Depends

from app.db.models.health import HealthResponse
from app.domain.entities.user import User
from app.security.dependencies import get_current_user
from app.domain.use_cases.health.check_health_status import CheckHealthStatusUseCase
from app.dependencies.use_cases import get_check_health_status_use_case
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
    use_case: CheckHealthStatusUseCase = Depends(get_check_health_status_use_case),
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
