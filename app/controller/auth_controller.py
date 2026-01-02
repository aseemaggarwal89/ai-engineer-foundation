from fastapi import APIRouter
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def issue_token(user_id: str):
    return {"access_token": create_access_token(user_id)}
