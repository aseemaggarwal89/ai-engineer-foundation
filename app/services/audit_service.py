# flake8: noqa: E501

import logging

from app.domain.audit_event import AuditEvent
from app.domain.event_type import EventType
from app.repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, repo: AuditRepository):
        self._repo = repo

    async def log_login(self, user_id: str) -> None:
        await self.log_event(user_id, EventType.USER_LOGIN)

    async def log_event(self, user_id: str, event_type: EventType) -> None:
        logger.info("AUDIT TASK STARTED", extra={"user_id": user_id, "event_type": event_type})
        try:
            event = AuditEvent(
                user_id=user_id,
                event_type=event_type
            )
            await self._repo.create_event(event)
        except Exception:
            logger.exception(
                "Audit log failed",
                extra={"user_id": user_id}
            )
