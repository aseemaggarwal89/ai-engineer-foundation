from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.deps import get_db_session
from app.domain.interfaces.health_repository import HealthRepository
from app.domain.interfaces.user_repository import UserRepository
from app.repositories.health_repository import HealthRepositoryImpl
from app.repositories.user_repository import SQLAlchemyUserRepository


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """
    Infrastructure wiring.
    Router does NOT know the concrete repository.
    """
    return SQLAlchemyUserRepository(session)


def get_health_repository(
    session: AsyncSession = Depends(get_db_session),
) -> HealthRepository:
    """
    Infrastructure wiring.
    Router does NOT know the concrete repository.
    """
    return HealthRepositoryImpl(session)
