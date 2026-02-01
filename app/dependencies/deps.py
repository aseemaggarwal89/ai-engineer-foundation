from functools import lru_cache
from fastapi import Depends
from app.application.ai.parsers.bullet_parser import BulletParser
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.application.ai.services.summary_service import SummaryService
from app.core.config import AISettings, Settings, get_settings
from app.infrastructure.ai.openai_adapter import OpenAIAdapter
from app.services.audit_service import AuditService
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_repository import AuditRepository
from app.db.db import AsyncSessionLocal
from openai import AsyncOpenAI

# -------------------------
# Core / App-Level
# -------------------------


@lru_cache
def settings():
    return get_settings()


def get_ai_settings(
    settings: Settings = Depends(get_settings),
) -> AISettings:
    return settings.ai


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


def get_openai_client(
        ai_settings: AISettings = Depends(get_ai_settings),
):
    return AsyncOpenAI(api_key=ai_settings.openai_api_key)


def get_ai_model(
        ai_settings: AISettings = Depends(get_ai_settings),
):
    return OpenAIAdapter(get_openai_client, ai_settings)


def get_summary_service(
        model=Depends(get_ai_model),
        ai_settings: AISettings = Depends(get_ai_settings),
):
    return SummaryService(
        model=model, prompt=SummaryPrompt(), parser=BulletParser(), settings=ai_settings
    )
