from fastapi import Depends, HTTPException, status

from app.db.models.user import User
from app.domain.role import Role
from app.dependencies.deps import get_current_active_user
from app.domain.exceptions import AuthenticationError


def require_role(required_role: Role):
    """
    Dependency factory that enforces a minimum role.
    """

    def _role_guard(
        user: User = Depends(get_current_active_user),
    ) -> User:
        if user.role != required_role:
            raise AuthenticationError("Insufficient permissions")
            # raise HTTPException(
            #     status_code=status.HTTP_403_FORBIDDEN,
            #     detail="Insufficient permissions",
            # )
        return user

    return _role_guard

# def require_roles(*allowed_roles: Role):
#     def _guard(user: User = Depends(get_current_active_user)) -> User:
#         if user.role not in allowed_roles:
#             raise HTTPException(status_code=403, detail="Forbidden")
#         return user
#     return _guard