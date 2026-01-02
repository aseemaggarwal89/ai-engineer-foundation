from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.health import HealthStatus


class HealthRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_status(self) -> str:
        result = await self._session.execute(
            select(HealthStatus).limit(1)
        )
        row = result.scalar_one_or_none()

        if row is None:
            status = HealthStatus(status="ok")
            self._session.add(status)
            await self._session.commit()
            return "ok"

        return row.status
