# flake8: noqa

import sys
from pathlib import Path

# 🔴 MUST BE FIRST
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))


from contextlib import asynccontextmanager
import logging
import asyncio
import uvicorn
from fastapi import FastAPI

from app.core.logging import setup_logging
from app.core.config import get_settings
from app.controller.health_controller import router as health_router
from app.controller.auth_controller import router as auth_router
from app.core.error_handlers import (
    app_exception_handler,
    not_found_exception_handler,
    service_exception_handler,
)
from app.core.exceptions import AppException, NotFoundError, ServiceError
from app.core.db import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --------------------
    # Startup
    # --------------------
    # logging.getLogger(__name__).info("Initializing database")
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield  # Application runs here

    # --------------------
    # Shutdown (future use)
    # --------------------
    logging.getLogger(__name__).info("Application shutdown")

    
def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.environment == "local",
        lifespan=lifespan,
    )

    # --------------------
    # Routers
    # --------------------
    app.include_router(health_router)
    app.include_router(auth_router)

    # --------------------
    # Global Exception Handlers
    # --------------------
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(ServiceError, service_exception_handler)

    return app


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    logging.getLogger(__name__).info("Starting FastAPI service")

    app = create_app()
    
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level=settings.log_level.lower(),
        lifespan="on",   # Enable lifespan events
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
