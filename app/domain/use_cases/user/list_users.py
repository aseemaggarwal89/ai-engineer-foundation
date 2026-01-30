import logging
from typing import List
from app.core.tracer import traced
from app.domain.interfaces.user_repository import UserRepository
from app.domain.entities.user import User

logger = logging.getLogger(__name__)


class ListUsersUseCase:
    """
    Retrieve all users.
    Only ADMIN users are allowed.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    @traced("usecase.list_users")
    async def execute(self) -> List[User]:
        """
        Retrieve all users.

        Authorization is enforced at the API layer.
        """

        # 1️⃣ Attempt (low noise)
        logger.debug(
            "Listing users",
            extra={
                "event": "list_users_attempt",
            },
        )

        users = await self.user_repo.list_all()

        # 2️⃣ Result summary (important, but not noisy)
        logger.info(
            "Users listed successfully",
            extra={
                "event": "list_users_success",
                "user_count": len(users),
            },
        )

        return users
