from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from sqlalchemy import select


class UserRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self._session = session

    async def get_by_id(self, user_id: str) -> User | None:
        return await self._session.get(User, user_id)
    
    async def save(self, user: User) -> User:
        # Push INSERT to DB (gets PK)
        self._session.add(user)
        await self._session.flush()

        # Load DB-generated fields (id, created_at, etc.)
        await self._session.refresh(user)

        # Commit transaction
        await self._session.commit()

        return user
    
    async def list_all_users(self) -> list[User]:
        result = await self._session.execute(
            select(User)
        )
        return result.scalars().all()
