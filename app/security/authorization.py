from fastapi import Depends

from app.db.models.user_orm import UserORM
from app.domain.entities.user import User
from app.domain.entities.user_role import UserRole
from app.security.dependencies import get_current_active_user
from app.domain.exceptions.exceptions import AuthorizationError


def require_role(required_role: UserRole):
    """
    Dependency factory that enforces a single required role.
    """

    def _role_guard(
        user: User = Depends(get_current_active_user),
    ) -> User:
        if user.role != required_role:
            raise AuthorizationError("Insufficient permissions")
        return user

    return _role_guard


def require_any_role(*allowed_roles: UserRole):
    """
    Dependency factory that enforces one of the allowed roles.
    """

    def _role_guard(
        user: User = Depends(get_current_active_user),
    ) -> User:
        if user.role not in allowed_roles:
            raise AuthorizationError("Insufficient permissions")
        return user

    return _role_guard