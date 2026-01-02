from functools import lru_cache
from fastapi.params import Depends
from app.core.db import get_db_session
from app.core.config import get_settings
from app.repositories.health_repository import HealthRepository
from app.services.health_protocol import HealthServiceProtocol
from app.services.health_service import HealthService
from sqlalchemy.ext.asyncio import AsyncSession


@lru_cache
def settings():
    return get_settings()


def health_repository(
    session: AsyncSession = Depends(get_db_session),
) -> HealthRepository:
    return HealthRepository(session)


def health_service(
    repo: HealthRepository = Depends(health_repository),
) -> HealthServiceProtocol:
    return HealthService(repo)