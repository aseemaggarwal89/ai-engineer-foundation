from fastapi import Depends
from app.domain.interfaces.health_repository import HealthRepository
from app.domain.use_cases.health.check_health_status import CheckHealthStatusUseCase
from app.domain.use_cases.user.get_current_user import GetCurrentUserUseCase
from app.domain.use_cases.user.list_users import ListUsersUseCase
from app.domain.use_cases.user.register_user import RegisterUserUseCase
from app.domain.use_cases.user.login_user import LoginUserUseCase

from app.domain.interfaces.user_repository import UserRepository
from app.dependencies.repositories import (
    get_user_repository,
    get_health_repository,
)


def get_register_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> RegisterUserUseCase:
    """
    Application wiring at the boundary.
    """
    return RegisterUserUseCase(user_repo)


def get_login_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> LoginUserUseCase:
    """
    Application wiring at the boundary.
    """
    return LoginUserUseCase(user_repo)


def get_current_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> GetCurrentUserUseCase:
    """
    Application wiring at the boundary.
    """
    return GetCurrentUserUseCase(user_repo)


def get_list_users_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> ListUsersUseCase:
    """
    Application wiring at the boundary.
    """
    return ListUsersUseCase(user_repo)


def get_check_health_status_use_case(
    repo: HealthRepository = Depends(get_health_repository),
) -> CheckHealthStatusUseCase:
    return CheckHealthStatusUseCase(repo)