from fastapi import APIRouter, Depends, BackgroundTasks, status
from app.domain.entities.user import User
from app.domain.entities.user_role import UserRole
from app.domain.use_cases.user.list_users import ListUsersUseCase
from app.schemas.user import UserListResponse, UserRegisterRequest, UserResponse
from app.domain.use_cases.user.register_user import RegisterUserUseCase
from app.dependencies.use_cases import (
    get_list_users_use_case, 
    get_register_user_use_case
)
from app.security.authorization import require_role
from app.services.audit_service import AuditService
from app.dependencies.deps import get_audit_service
from app.domain.event_type import EventType
from app.security.dependencies import (
    get_current_active_user,
    get_current_user,
)

from app.domain.use_cases.user.login_user import LoginUserUseCase
from app.schemas.auth import LoginRequest, TokenResponse

from app.dependencies.use_cases import get_login_user_use_case
from app.security.jwt import create_access_token

# ---------------------------------------------------------------------
# Public routes (no authentication)
# ---------------------------------------------------------------------

public_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@public_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserRegisterRequest,
    background_tasks: BackgroundTasks,
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Domain exceptions are handled globally.
    """

    user = await use_case.execute(
        email=user_data.email,
        password=user_data.password,
    )

    background_tasks.add_task(
        audit_service.log_event,
        user_id=user.id,
        event_type=EventType.USER_REGISTERED,
    )

    return UserResponse.from_domain(user)


@public_router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    background_tasks: BackgroundTasks,
    use_case: LoginUserUseCase = Depends(get_login_user_use_case),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Issue an access token for an existing user.
    Domain exceptions are handled globally.
    """

    user = await use_case.execute(
        email=data.email,
        password=data.password,
    )

    token = create_access_token(user)

    background_tasks.add_task(
        audit_service.log_login,
        user.id,
    )

    return TokenResponse(access_token=token)


# ---------------------------------------------------------------------
# Protected routes (authentication required)
# ---------------------------------------------------------------------

protected_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(get_current_active_user)],
)


@protected_router.get(
    "/me",
    response_model=UserResponse,
)
async def me(
    user: User = Depends(get_current_user),
):
    return UserResponse.from_domain(user)


@protected_router.get(
    "/users",
    response_model=UserListResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))]
)
async def read_users(
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
):
    """
    Retrieve all users.

    Authorization is enforced at the router level.
    """
    users = await use_case.execute()
    return UserListResponse.from_domain(users)
