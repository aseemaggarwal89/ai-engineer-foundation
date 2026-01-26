from fastapi import APIRouter, Depends

from app.db.models.user import User
from app.domain.role import Role
from app.dependencies.authorization import require_role

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/dashboard")
async def admin_dashboard(
    _: User = Depends(require_role(Role.ADMIN)),
):
    return {"message": "Welcome, admin"}
