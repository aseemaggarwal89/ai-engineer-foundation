from app.domain.interfaces.user_repository import UserRepository
from app.domain.entities.user import User
from typing import List


class ListUsersUseCase:
    """
    Retrieve all users.
    Only ADMIN users are allowed.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self) -> List[User]:
        """
        Retrieve all users.

        This method assumes authorization has already been enforced
        at the API dependency layer.
        """
        return await self.user_repo.list_all()
