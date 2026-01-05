from dataclasses import dataclass
from datetime import datetime
from app.domain.event_type import EventType
from app.models.audit_orm import AuditORM


@dataclass(frozen=True)
class AuditEvent:
    user_id: str
    event_type: EventType
    created_at: datetime | None = None


def to_orm(event: AuditEvent) -> AuditORM:
    return AuditORM(
        user_id=event.user_id,
        event_type=event.event_type.value
    )
