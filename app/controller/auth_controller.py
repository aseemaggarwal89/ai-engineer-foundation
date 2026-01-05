from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.dependencies.deps import get_audit_service, get_auth_service
from app.domain.errors import UserAlreadyExistsError
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.domain.user import UserRegisterRequest, UserReadResponse
from app.domain.event_type import EventType

router = APIRouter(prefix="/auth", tags=["auth"])


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


@router.post("/register", 
             response_class=UserReadResponse, 
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