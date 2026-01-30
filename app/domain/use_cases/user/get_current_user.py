import logging
from uuid import UUID
from app.core.tracer import traced
from app.domain.interfaces.user_repository import UserRepository
from app.domain.entities.user import User
from app.domain.exceptions.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class GetCurrentUserUseCase:

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    @traced("usecase.get_current_user")
    async def execute(self, user_id: UUID | str) -> User:
        """
        Resolve the current authenticated user from the JWT payload.

        - Token validation is handled upstream
        - This use case enforces business validity
        """

        # 1️⃣ Resolution attempt (low-noise)
        logger.debug(
            "Resolving current user",
            extra={
                "event": "current_user_resolve_attempt",
                "user_id": str(user_id),
            },
        )

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            # 2️⃣ User not found
            logger.warning(
                "Current user resolution failed: user not found",
                extra={
                    "event": "current_user_resolve_failed",
                    "reason": "user_not_found",
                    "user_id": str(user_id),
                },
            )
            raise NotFoundError(
                f"Active user with id '{user_id}' not found"
            )

        if not user.is_active:
            # 3️⃣ User inactive
            logger.warning(
                "Current user resolution failed: inactive user",
                extra={
                    "event": "current_user_resolve_failed",
                    "reason": "user_inactive",
                    "user_id": str(user.id),
                },
            )
            raise NotFoundError(
                f"Active user with id '{user_id}' not found"
            )

        # 4️⃣ Successful resolution (debug only)
        logger.debug(
            "Current user resolved successfully",
            extra={
                "event": "current_user_resolved",
                "user_id": str(user.id),
                "role": user.role.value,
            },
        )

        return user
