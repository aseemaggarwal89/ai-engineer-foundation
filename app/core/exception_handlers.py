"""
HTTP exception handlers.

These handlers translate domain exceptions into HTTP responses.
They are registered once at application startup.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from app.domain.exceptions import (
    AppException, NotFoundError, ServiceError, AuthenticationError
)


async def app_exception_handler(request: Request, exc: AppException):
    """
    Handles all AppException-based errors.

    Ensures a consistent error response structure across the API.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )


async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """
    Explicit handler for NotFoundError.
    (Optional, but useful if you want custom logging or metrics.)
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )


async def service_exception_handler(request: Request, exc: ServiceError):
    """
    Handler for unexpected internal service failures.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )


async def auth_exception_handler(
    request: Request,
    exc: AuthenticationError,
):
    return JSONResponse(
        status_code=401,
        content={
            "detail": exc.message,
            "code": exc.error_code or "AUTH_401",
        },
    )