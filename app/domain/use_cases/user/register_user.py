from uuid import uuid4

from app.domain.entities.user import User
from app.domain.entities.user_role import UserRole
from app.domain.interfaces.user_repository import UserRepository
from app.domain.exceptions.exceptions import UserAlreadyExistsError
from app.security.password import hash_password


class RegisterUserUseCase:

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(
        self, email: str, password: str,
        role: UserRole = UserRole.USER
    ) -> User:
        """
        Register a new user.

        Business rules:
        - User ID must be unique

        Raises:
            UserAlreadyExistsError: if a user with the same ID already exists
        """
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(f"User with email {email} already exists")

        user = User(
            id=uuid4(),
            email=email,
            is_active=True,
            role=role,
        )

        # Persist user and return the saved entity
        return await self.user_repo.create(
            user=user,
            password_hash=hash_password(password),
        )
