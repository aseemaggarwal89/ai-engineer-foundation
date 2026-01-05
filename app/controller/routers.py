from fastapi import FastAPI
from app.controller.health_controller import router as health_router
from app.controller.auth_controller import router as auth_router
from app.core.error_handlers import (
    app_exception_handler,
    not_found_exception_handler,
    service_exception_handler,
)
from app.core.exceptions import AppException, NotFoundError, ServiceError


def addRouters(app: FastAPI):
    # --------------------
    # Routers
    # --------------------
    app.include_router(health_router)
    app.include_router(auth_router)


def addGlobalExceptionHandlers(app: FastAPI):
    # --------------------
    # Global Exception Handlers
    # --------------------
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(ServiceError, service_exception_handler)