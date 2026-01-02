import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException, NotFoundError, ServiceError

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException):
    logger.error("Application error: %s", exc.message)
    return JSONResponse(
        status_code=400,
        content={"error": exc.message},
    )


async def not_found_exception_handler(request: Request, exc: NotFoundError):
    logger.warning("Not found: %s", exc.message)
    return JSONResponse(
        status_code=404,
        content={"error": exc.message},
    )


async def service_exception_handler(request: Request, exc: ServiceError):
    logger.exception("Service failure", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
