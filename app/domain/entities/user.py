from dataclasses import dataclass
from uuid import UUID
from app.domain.entities.user_role import UserRole


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    is_active: bool
    role: UserRole
    password_hash: str = ""  # Optional, can be excluded when not needed
