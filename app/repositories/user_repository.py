from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.timeout import timeout
from app.core.retry import db_retry
from app.db.models.user_orm import UserORM
from app.dependencies.deps import settings
from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepository
from app.repositories.mappers.user_mapper import orm_to_domain_user

cfg = settings()


class SQLAlchemyUserRepository(UserRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    @db_retry()
    @timeout(seconds=cfg.db_timeout_seconds)
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM).where(UserORM.id == str(user_id))
        )
        orm_user = result.scalar_one_or_none()
        return orm_to_domain_user(orm_user) if orm_user else None

    @db_retry()
    @timeout(seconds=cfg.db_timeout_seconds)
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM).where(UserORM.email == email)
        )
        orm_user = result.scalar_one_or_none()
        return orm_to_domain_user(orm_user) if orm_user else None

    @db_retry()
    @timeout(seconds=cfg.db_timeout_seconds) 
    async def create(
        self,
        user: User,
        password_hash: str,
    ) -> User:
        orm_user = UserORM(
            id=str(user.id),
            email=user.email,
            is_active=user.is_active,
            role=user.role,
            password_hash=password_hash,
        )

        # Push INSERT to DB (gets PK)
        self._session.add(orm_user)
        await self._session.flush()

        # Load DB-generated fields (id, created_at, etc.)
        await self._session.refresh(orm_user)

        # Commit transaction
        await self._session.commit()

        return orm_to_domain_user(orm_user)
    
    @db_retry()
    @timeout(seconds=cfg.db_timeout_seconds)
    async def update(self, user: User) -> User:
        """
        Save assumes the user already exists OR is created elsewhere.
        This method persists state, not credentials.
        """
        orm_user = await self._session.get(UserORM, str(user.id))

        if orm_user is None:
            raise ValueError("Cannot save non-existing user")

        orm_user.email = user.email
        orm_user.is_active = user.is_active
        orm_user.role = user.role

        await self._session.commit()
        await self._session.refresh(orm_user)

        return orm_to_domain_user(orm_user)

    @db_retry()
    @timeout(seconds=cfg.db_timeout_seconds)
    async def list_all(self) -> List[User]:
        result = await self._session.execute(select(UserORM))
        return [orm_to_domain_user(u) for u in result.scalars().all()]
    

# class UserRepository:
#     def __init__(
#         self,
#         session: AsyncSession,
#     ):
#         self._session = session

#     async def get_by_id(self, user_id: str) -> UserORM | None:
#         result = await self._session.execute(
#             select(UserORM).where(UserORM.id == user_id)
#         )
#         return result.scalar_one_or_none()
    
#     async def get_by_email(self, email: str) -> UserORM | None:
#         result = await self._session.execute(
#             select(UserORM).where(UserORM.email == email)
#         )
#         return result.scalar_one_or_none()
    
    # async def save(self, user: UserORM) -> UserORM:
    #     # Push INSERT to DB (gets PK)
    #     self._session.add(user)
    #     await self._session.flush()

    #     # Load DB-generated fields (id, created_at, etc.)
    #     await self._session.refresh(user)

    #     # Commit transaction
    #     await self._session.commit()

    #     return user
    
#     async def list_all_users(self) -> list[UserORM]:
#         result = await self._session.execute(
#             select(UserORM)
#         )
#         return result.scalars().all()
