from fastapi import FastAPI

from app.routers.health import (
    public_router as health_public_router,
    protected_router as health_protected_router,
)
from app.routers.auth import (
    public_router as auth_public_router,
    protected_router as auth_protected_router,
)

from app.routers.admin import (
    admin_router as admin_router
)


def addRouters(app: FastAPI) -> None:
    """
    Register all API routers.

    Routers are grouped into public and protected variants
    to enforce security boundaries consistently.
    """

    routers = [
        # Health
        health_public_router,
        health_protected_router,

        # Auth
        auth_public_router,
        auth_protected_router,

        # Admin
        admin_router
    ]

    for router in routers:
        app.include_router(router)
