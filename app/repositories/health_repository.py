from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import Settings
from app.core.timeout import timeout, timeout_from_self
from app.dependencies.deps import settings
from app.domain.interfaces.health_repository import HealthRepository
from app.db.models.health import HealthStatus


class HealthRepositoryImpl(HealthRepository):
    def __init__(self, session: AsyncSession,
                 app_settings: Settings):
        self._session = session
        self.timeout_seconds = app_settings.db_timeout_seconds

    @timeout_from_self
    async def fetch_status(self) -> str:

        result = await self._session.execute(select(HealthStatus).limit(1))
        row = result.scalar_one_or_none()

        if row is None:
            status = HealthStatus(status="ok")
            self._session.add(status)
            await self._session.commit()
            return "ok"

        return row.status
