# flake8: noqa: E501

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.dependencies.deps import get_audit_service, get_auth_service
from app.domain.errors import UserAlreadyExistsError
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.domain.user import UserListResponse, UserRegisterRequest
from app.domain.user import UserReadResponse
from app.domain.event_type import EventType
import logging

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)


@router.post("/token")
async def issue_token(user_id: str,
                      background_tasks: BackgroundTasks,
                      auth_service: AuthService = Depends(get_auth_service),
                      audit_service: AuditService = Depends(get_audit_service)):
    user = await auth_service.authenticate(user_id)
    token = auth_service.create_token(user)
    background_tasks.add_task(
        audit_service.log_login,
        user.id)
    return {"access_token": token}


@router.get("/users", response_model=UserListResponse)
async def read_users(auth_service: AuthService = Depends(get_auth_service),):
    # Placeholder for user listing logic
    users = await auth_service.read_users()
    return {"users": users}


@router.post("/register",
             response_model=UserReadResponse, 
             status_code=201)
async def register_user(user_data: UserRegisterRequest,
                        background_tasks: BackgroundTasks,
                        auth_service: AuthService = Depends(get_auth_service),
                        audit_service: AuditService = Depends(get_audit_service)):
    try:
        user = await auth_service.register_user(user_data)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    # Side-effect → background task
    background_tasks.add_task(
        audit_service.log_event,
        user_id=user.id,
        event_type=EventType.USER_REGISTERED,
    )

    return user