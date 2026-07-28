import logging
from dataclasses import dataclass

from app.core.tracer import traced
from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepository
from app.domain.exceptions.exceptions import AuthenticationError
from app.security.email import normalize_email
from app.security.jwt import create_access_token
from app.security.password import verify_password

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthenticationResult:
    user: User
    access_token: str


class LoginUserUseCase:
    """
    Authenticate an existing user using email + password.
    """

    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    @traced("usecase.login_user")
    async def execute(self, email: str, password: str) -> AuthenticationResult:
        normalized_email = normalize_email(email)

        # 1️⃣ Login attempt
        logger.info(
            "User login attempt",
            extra={
                "event": "user_login_attempt",
                "email": normalized_email,
            },
        )

        user = await self._user_repo.get_by_email(normalized_email)

        if not user:
            # 2️⃣ Authentication failure (user not found)
            logger.warning(
                "User login failed: invalid credentials",
                extra={
                    "event": "user_login_failed",
                    "reason": "user_not_found",
                    "email": normalized_email,
                },
            )
            raise AuthenticationError()

        if not verify_password(password, user.password_hash):
            # 3️⃣ Authentication failure (wrong password)
            logger.warning(
                "User login failed: invalid credentials",
                extra={
                    "event": "user_login_failed",
                    "reason": "invalid_password",
                    "user_id": str(user.id),
                },
            )
            raise AuthenticationError()

        if not user.is_active:
            # 4️⃣ Authentication failure (inactive account)
            logger.warning(
                "User login failed: inactive account",
                extra={
                    "event": "user_login_failed",
                    "reason": "inactive_account",
                    "user_id": str(user.id),
                },
            )
            raise AuthenticationError("User account is inactive")

        # 5️⃣ Login success
        logger.info(
            "User login successful",
            extra={
                "event": "user_login_success",
                "user_id": str(user.id),
                "role": user.role.value,
            },
        )

        return AuthenticationResult(
            user=user,
            access_token=create_access_token(user),
        )
