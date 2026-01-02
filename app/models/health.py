from pydantic import BaseModel

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class HealthResponse(BaseModel):
    status: str


class HealthStatus(Base):
    __tablename__ = "health_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(20))