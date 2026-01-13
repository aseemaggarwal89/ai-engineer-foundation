# flake8: noqa: E501

from collections.abc import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.audit_event import AuditEvent, to_orm
import logging

logger = logging.getLogger(__name__)


class AuditRepository:
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    async def create_event(self, event: AuditEvent) -> None:
        async with self._session_factory() as session:
            logger.debug("AUDIT create_event STARTED", extra={"session": session})
            audit_event = to_orm(event)            
            session.add(audit_event)

            # Push INSERT to DB (gets PK)
            await session.flush()

            # Load DB-generated fields (id, created_at, etc.)
            await session.refresh(audit_event)

            logger.debug("AUDIT create_event completed", extra={"audit": audit_event})

            # Commit transaction
            await session.commit()
        