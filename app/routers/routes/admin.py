from fastapi import APIRouter, Depends

from app.domain.entities.user import User
from app.domain.entities.user_role import UserRole
from app.security.authorization import require_role

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/dashboard")
async def admin_dashboard(
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    return {"message": "Welcome, admin"}
