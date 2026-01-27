from functools import lru_cache
from fastapi import Depends
from app.core.config import get_settings
from app.repositories.health_repository import HealthRepository
from app.services.audit_service import AuditService
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_repository import AuditRepository
from app.db.db import AsyncSessionLocal

# -------------------------
# Core / App-Level
# -------------------------


@lru_cache
def settings():
    return get_settings()

# -------------------------
# DB Session
# -------------------------


async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency that provides a transactional async DB session.
    """
    async with AsyncSessionLocal() as session:
        yield session

# -------------------------
# Repositories
# -------------------------


def get_audit_repository() -> AuditRepository:
    """
    Uses its own session factory to avoid coupling audit logging
    to the request lifecycle (safe for background/fire-and-forget).
    """
    return AuditRepository(session_factory=AsyncSessionLocal)


# -------------------------
# Services
# -------------------------

def get_audit_service(
    repo: AuditRepository = Depends(get_audit_repository),
) -> AuditService:
    return AuditService(repo)