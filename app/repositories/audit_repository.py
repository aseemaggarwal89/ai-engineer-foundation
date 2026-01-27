from collections.abc import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.audit_event import AuditEvent, to_orm
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class AuditRepository:
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    async def create_event(self, event: AuditEvent) -> None:
        async with self._session_factory() as session:
            logger.debug(
                "AUDIT create_event STARTED",
                extra={"event_type": event.event_type},
            )

            try:
                audit_event = to_orm(event)
                session.add(audit_event)

                await session.flush()
                await session.refresh(audit_event)
                await session.commit()

                logger.debug(
                    "AUDIT create_event completed",
                    extra={"audit_id": audit_event.id},
                )

            except SQLAlchemyError:
                await session.rollback()
                logger.exception("AUDIT create_event failed")
                raise