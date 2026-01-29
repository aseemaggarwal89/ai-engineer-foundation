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
        # 1️⃣ Audit attempt (important but not noisy)
        logger.info(
            "Audit event logging started",
            extra={
                "event": "audit_log_attempt",
                "audit_type": event_type.value,
                "user_id": user_id,
            },
        )

        try:
            audit_event = AuditEvent(
                user_id=user_id,
                event_type=event_type,
            )

            await self._repo.create_event(audit_event)

            # 2️⃣ Audit success
            logger.info(
                "Audit event logged successfully",
                extra={
                    "event": "audit_log_success",
                    "audit_type": event_type.value,
                    "user_id": user_id,
                },
            )

        except Exception as exc:
            # 3️⃣ Audit failure (never propagate)
            logger.error(
                "Audit event logging failed",
                extra={
                    "event": "audit_log_failed",
                    "audit_type": event_type.value,
                    "user_id": user_id,
                    "error_type": type(exc).__name__,
                },
            )
