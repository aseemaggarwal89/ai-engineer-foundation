from enum import Enum


class UserRole(str, Enum):
    """
    Application roles used for authorization.

    Keep this enum small and intentional.
    """
    USER = "USER"
    ADMIN = "ADMIN"

