import logging
from uuid import uuid4

from app.domain.entities.user import User
from app.domain.entities.user_role import UserRole
from app.domain.interfaces.user_repository import UserRepository
from app.domain.exceptions.exceptions import UserAlreadyExistsError
from app.security.password import hash_password

logger = logging.getLogger(__name__)


class RegisterUserUseCase:

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(
        self,
        email: str,
        password: str,
        role: UserRole = UserRole.USER,
    ) -> User:
        """
        Register a new user.
        """

        # 1️⃣ Intent log
        logger.info(
            "User registration attempt",
            extra={
                "event": "user_register_attempt",
                "email": email,
                "requested_role": role.value,
            },
        )

        existing = await self.user_repo.get_by_email(email)
        if existing:
            # 2️⃣ Business rule violation log
            logger.warning(
                "User registration failed: email already exists",
                extra={
                    "event": "user_register_conflict",
                    "email": email,
                },
            )
            raise UserAlreadyExistsError(
                f"User with email {email} already exists"
            )

        user = User(
            id=uuid4(),
            email=email,
            is_active=True,
            role=role,
        )

        created_user = await self.user_repo.create(
            user=user,
            password_hash=hash_password(password),
        )

        # 3️⃣ Success log
        logger.info(
            "User registered successfully",
            extra={
                "event": "user_registered",
                "user_id": str(created_user.id),
                "role": created_user.role.value,
            },
        )

        return created_user
