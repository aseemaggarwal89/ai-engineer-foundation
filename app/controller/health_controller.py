import logging
from fastapi import APIRouter, Depends

from app.models.health import HealthResponse
from app.services.health_protocol import HealthServiceProtocol
from app.dependencies.deps import health_service
from app.dependencies.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def root():
    return {"message": "FastAPI service is running"}


@router.get("/health", response_model=HealthResponse)
async def health_check(
    service: HealthServiceProtocol = Depends(health_service),
    user_id: str = Depends(get_current_user),
) -> HealthResponse:
    logger.debug("Health check endpoint called")

    status = await service.check()
    return HealthResponse(status=f"{status} (user={user_id})")