from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    String, Boolean, Enum as SAEnum
)
from app.db.db import Base
from app.domain.role import Role


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    role: Mapped[Role] = mapped_column(
        SAEnum(Role, name="user_role"),
        default=Role.USER,
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