# flake8: noqa: E501

import logging
from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.db.models.user import User
from app.dependencies.deps import (
    get_auth_service,
    get_audit_service,
    get_current_active_user,
    get_current_user,
)
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.domain.user_domain import (
    UserListResponse,
    UserRegisterRequest,
    UserReadResponse,
)
from app.domain.event_type import EventType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Public routes (NO authentication required)
# ---------------------------------------------------------------------

public_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@public_router.post("/token")
async def issue_token(
    user_id: str,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Issue an access token for an existing user.
    """
    user = await auth_service.authenticate(user_id)
    token = auth_service.create_token(user)

    background_tasks.add_task(
        audit_service.log_login,
        user.id,
    )

    return {"access_token": token}


@public_router.post(
    "/register",
    response_model=UserReadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserRegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Register a new user.

    Domain exceptions (e.g. UserAlreadyExistsError)
    are handled by global exception handlers.
    """
    user = await auth_service.register_user(user_data)

    background_tasks.add_task(
        audit_service.log_event,
        user_id=user.id,
        event_type=EventType.USER_REGISTERED,
    )

    return user


# ---------------------------------------------------------------------
# Protected routes (AUTHENTICATION REQUIRED)
# ---------------------------------------------------------------------

protected_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    # 🔐 Router-level security guard
    dependencies=[Depends(get_current_active_user)],
)


@protected_router.get(
    "/me",
    response_model=UserReadResponse,
)
async def me(
    current_user: User = Depends(get_current_user),
):
    """
    Return the currently authenticated user.

    Security and user resolution are handled by dependencies.
    """
    return current_user


@protected_router.get(
    "/users",
    response_model=UserListResponse,
)
async def read_users(
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Retrieve all users.

    Authorization is enforced at the router level.
    """
    users = await auth_service.read_users()
    return {"users": users}
