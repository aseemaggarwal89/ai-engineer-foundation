from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean
from app.db.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
