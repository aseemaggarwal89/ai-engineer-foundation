from app.repositories.user_repository import UserRepository
from app.domain.user import UserRegisterRequest
from app.domain.errors import UserAlreadyExistsError
from app.core.security import create_access_token
from app.models.user import User


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository
    ):
        self._user_repo = user_repo

    async def authenticate(self, user_id: str) -> User:
        user = await self._user_repo.get_by_id(user_id)

        if not user:
            raise ValueError("Invalid user")

        # Add more checks here if needed:
        # - is_active
        # - password / OTP / biometric verification
        return user
    
    async def register_user(self, user_data: UserRegisterRequest) -> User:
        existing_user = await self._user_repo.get_by_id(user_data.id)

        if existing_user:
            raise UserAlreadyExistsError(
                f"User with id '{user_data.id}' already exists"
            )
        
        # Implement user registration logic here
        return await self._user_repo.save(user_data.to_model())
        
    def create_token(self, user: User) -> str:
        return create_access_token(subject=user.id)
    
    async def read_users(self) -> list[User]:
        # Placeholder for user listing logic
        users = await self._user_repo.list_all_users()
        return users