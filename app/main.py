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
from app.db.db import engine, Base
from app.core.exception_registry import addGlobalExceptionHandlers
from app.routers.routers import addRouters
from app.core.model_registry import ModelRegistry

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --------------------
    # Startup
    # --------------------
    logger.info("Application startup")
    registry = ModelRegistry()
    await registry.load()
    app.state.model_registry = registry

    # logging.getLogger(__name__).info("Initializing database")
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield  # Application runs here

    # --------------------
    # Shutdown (future use)
    # --------------------
    await registry.close()
    logger.info("Application shutdown")

    
def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("Starting FastAPI service")
    app = FastAPI(
        title=settings.app_name,
        debug=settings.environment == "local",
        lifespan=lifespan,
    )

    addRouters(app)
    addGlobalExceptionHandlers(app)
    return app


# ✅ THIS IS WHAT UVICORN IMPORTS
app = create_app()

async def main() -> None:
    settings = get_settings()
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
