from functools import lru_cache
from multiprocessing import AuthenticationError
from fastapi import Depends
from app.db.db import get_db_session
from app.core.config import get_settings
from app.dependencies.security import get_token_payload
from app.repositories.health_repository import HealthRepository
from app.repositories.user_repository import UserRepository
from app.services.health_protocol import HealthServiceProtocol
from app.services.health_service import HealthService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_repository import AuditRepository
from app.db.db import AsyncSessionLocal
from app.db.models.user import User


# -------------------------
# Core / App-Level
# -------------------------

@lru_cache
def settings():
    return get_settings()


# -------------------------
# Repositories
# -------------------------


def health_repository(
    session: AsyncSession = Depends(get_db_session),
) -> HealthRepository:
    return HealthRepository(session)


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)


def get_audit_repository() -> AuditRepository:
    """
    Uses its own session factory to avoid coupling audit logging
    to the request lifecycle (safe for background/fire-and-forget).
    """
    return AuditRepository(session_factory=AsyncSessionLocal)


# -------------------------
# Services
# -------------------------

def health_service(
    repo: HealthRepository = Depends(health_repository),
) -> HealthServiceProtocol:
    return HealthService(repo)


def get_auth_service(
    repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repo)


def get_audit_service(
    repo: AuditRepository = Depends(get_audit_repository),
) -> AuditService:
    return AuditService(repo)


# -------------------------
# Security / Auth
# -------------------------

async def get_current_user(
    payload: dict = Depends(get_token_payload),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token")

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_active:
        raise AuthenticationError("Inactive user")
    return user