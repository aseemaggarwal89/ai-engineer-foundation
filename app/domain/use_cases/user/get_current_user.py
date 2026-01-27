from uuid import UUID
from app.domain.interfaces.user_repository import UserRepository
from app.domain.entities.user import User
from app.domain.exceptions.exceptions import (
    AuthenticationError,
    NotFoundError,
)


class GetCurrentUserUseCase:

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID | str) -> User:
        """
        Resolve the current authenticated user from the JWT payload.

        - Token validation is handled by get_token_payload
        - Business validation is delegated to GetCurrentUserUseCase
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise NotFoundError(f"Active user with id '{user_id}' not found")

        return user
