from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from app.domain.entities.user import User


class UserRepository(ABC):

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def list_all(self) -> list[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def create(
        self,
        user: User,
        password_hash: str,
    ) -> User:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass

    # @abstractmethod
    # async def deactivate(self, user_id: UUID) -> None:
    #     pass

    # @abstractmethod
    # async def update_role(self, user_id: UUID, role: str) -> None:
    #     pass
