from fastapi import Depends
from app.domain.entities.user import User
from app.domain.exceptions.exceptions import AuthenticationError
from app.domain.use_cases.user.get_current_user import GetCurrentUserUseCase
from app.dependencies.use_cases import get_current_user_use_case
from app.security.security import get_token_payload

# -------------------------
# Security / Auth
# -------------------------


async def get_current_user(
    payload: dict = Depends(get_token_payload),
    current_user_use_case: GetCurrentUserUseCase = Depends(get_current_user_use_case),
) -> User:
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token")

    return await current_user_use_case.execute(user_id)


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_active:
        raise AuthenticationError("Inactive user")
    return user


