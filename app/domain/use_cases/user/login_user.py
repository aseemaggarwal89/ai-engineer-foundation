from app.domain.interfaces.user_repository import UserRepository
from app.domain.exceptions.exceptions import AuthenticationError
from app.security.password import verify_password


class LoginUserUseCase:
    """
    Authenticate an existing user using email + password.
    """

    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def execute(self, email: str, password: str):
        user = await self._user_repo.get_by_email(email)

        if not user:
            raise AuthenticationError()

        if not verify_password(password, user.password_hash):
            raise AuthenticationError()

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user