from functools import lru_cache
from fastapi.params import Depends
from app.core.db import get_db_session
from app.core.config import get_settings
from app.repositories.health_repository import HealthRepository
from app.repositories.user_repository import UserRepository
from app.services.health_protocol import HealthServiceProtocol
from app.services.health_service import HealthService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_repository import AuditRepository
from app.core.db import AsyncSessionLocal


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


def get_audit_repository() -> AuditRepository:
    return AuditRepository(session_factory=AsyncSessionLocal)


def get_audit_service(
        repo: AuditRepository = Depends(get_audit_repository)) -> AuditService:
    return AuditService(repo)


def get_user_repository(
        session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)


def get_auth_service(
        repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(repo)
