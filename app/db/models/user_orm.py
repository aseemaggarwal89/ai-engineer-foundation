import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    String, Boolean, Enum as SAEnum
)
from app.db.db import Base
from app.domain.entities.user_role import UserRole


class UserORM(Base):    
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
