from functools import lru_cache
from fastapi import Depends, HTTPException, Request, status
from app.db.db import get_db_session
from app.core.config import get_settings
from app.domain.exceptions import AuthenticationError
from app.repositories.health_repository import HealthRepository
from app.repositories.user_repository import UserRepository
from app.services.health_protocol import HealthServiceProtocol
from app.services.health_service import HealthService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_repository import AuditRepository
from app.db.db import AsyncSessionLocal

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security.jwt import decode_token
from app.db.models.user import User


# -------------------------
# Core / App-Level
# -------------------------

@lru_cache
def settings():
    return get_settings()


_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="JWT"
)


async def security(request: Request) -> HTTPAuthorizationCredentials:
    creds = await _bearer(request)

    if not creds:
        raise AuthenticationError("Missing token")
    
    return creds

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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user