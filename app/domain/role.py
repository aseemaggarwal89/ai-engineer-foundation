from enum import Enum


class Role(str, Enum):
    """
    Application roles used for authorization.

    Keep this enum small and intentional.
    """
    USER = "USER"
    ADMIN = "ADMIN"