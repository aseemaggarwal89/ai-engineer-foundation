"""
Registers global exception handlers with the FastAPI application.
"""

from fastapi import FastAPI
from app.domain.exceptions import (
    AppException, NotFoundError, ServiceError, AuthenticationError
)
from app.core.exception_handlers import (
    app_exception_handler,
    auth_exception_handler,
    not_found_exception_handler,
    service_exception_handler,
)


def addGlobalExceptionHandlers(app: FastAPI):
    """
    Register all global exception handlers.

    This should be called exactly once during app startup.
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(ServiceError, service_exception_handler)
    app.add_exception_handler(AuthenticationError, auth_exception_handler)