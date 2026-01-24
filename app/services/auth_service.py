
from app.repositories.user_repository import UserRepository
from app.domain.user_domain import UserRegisterRequest
from app.domain.exceptions import UserAlreadyExistsError, NotFoundError
from app.security.jwt import create_access_token
from app.db.models.user import User


class AuthService:
    """
    Authentication and user-related business logic.

    Responsibilities:
    - User authentication
    - User registration
    - Token creation
    - User retrieval for API consumers

    This service is domain-focused and contains NO HTTP concerns.
    All errors are raised as domain exceptions and translated at the API layer.
    """

    def __init__(self, user_repo: UserRepository):
        # Repository abstraction for persistence operations
        self._user_repo = user_repo

    async def authenticate(self, user_id: str) -> User:
        # flake8: noqa: E501
        """
        Authenticate a user by user_id.

        This method performs identity validation only.
        It does NOT handle transport-level concerns (headers, tokens, HTTP codes).

        Raises:
            NotFoundError: if the user does not exist
        """
        user = await self._user_repo.get_by_id(user_id)

        if not user:
            # Domain-level failure → handled by global exception handler
            raise NotFoundError(f"User with id '{user_id}' not found")

        # Additional checks can be added here:
        # - user.is_active
        # - password / OTP validation
        # - biometric verification
        return user

    async def register_user(self, user_data: UserRegisterRequest) -> User:
        """
        Register a new user.

        Business rules:
        - User ID must be unique

        Raises:
            UserAlreadyExistsError: if a user with the same ID already exists
        """
        existing_user = await self._user_repo.get_by_id(user_data.id)

        if existing_user:
            raise UserAlreadyExistsError(
                f"User with id '{user_data.id}' already exists"
            )

        # Convert domain request object into persistence model
        user_model = user_data.to_model()

        # Persist user and return the saved entity
        return await self._user_repo.save(user_model)

    def create_token(self, user: User) -> str:
        """
        Create a JWT access token for the authenticated user.

        Token creation is intentionally synchronous:
        - No I/O
        - Pure computation
        """
        return create_access_token(subject=user.id)

    async def read_users(self) -> list[User]:
        """
        Retrieve all users.

        This method assumes authorization has already been enforced
        at the API dependency layer.
        """
        return await self._user_repo.list_all_users()
    
    async def get_active_user_by_id(self, user_id: str) -> User:
        """
        Retrieve an active user by user_id.

        Raises:
            NotFoundError: if the user does not exist or is inactive
        """
        user = await self._user_repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise NotFoundError(f"Active user with id '{user_id}' not found")

        return user

