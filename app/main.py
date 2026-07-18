# flake8: noqa

import sys
from pathlib import Path

from app.application.ai.core.container import ServiceContainer
from app.core.middleware.body_size import BodySizeLimitMiddleware
from app.core.middleware.metrics_middleware import MetricsMiddleware

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
from app.api.routers import addRouters
from app.core.middleware.request_id import RequestIDMiddleware

from app.core.tracing import setup_tracing

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --------------------
    # Startup
    # --------------------
    logger.info("Application startup")
    settings = get_settings()
    container = ServiceContainer(settings)
    await container.startup()
    app.state.container = container

    logging.getLogger(__name__).info("Initializing database")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ✅ Create once
    yield  # Application runs here

    # --------------------
    # Shutdown (future use)
    # --------------------
    await container.shutdown()
    logger.info("Application shutdown")

    
def create_app() -> FastAPI:
    settings = get_settings()

    # 1️⃣ Logging first (everything after uses it)
    setup_logging(settings.log_level)
    logger.info(
    "FastAPI service starting",
    extra={
        "event": "service_startup",
        "environment": settings.environment,
        "app_name": settings.app_name,
        "model": settings.ai.model_name,
    },
    )

    # 3️⃣ Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        debug=settings.environment == "local",
        lifespan=lifespan,
    )

    # 2️⃣ Tracing second (captures startup + routes)
    if settings.ai.otlp_endpoint:
        setup_tracing(app, settings.app_name, settings.ai.otlp_endpoint)

    # 4️⃣ Middleware (order matters)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # metrics wrapper
    app.add_middleware(MetricsMiddleware)

    # request id first → available to logs + traces
    app.add_middleware(RequestIDMiddleware)

    app.add_middleware(
    BodySizeLimitMiddleware,
    max_body_size=settings.ai.max_request_bytes,
    )
    
    # 5️⃣ Routers
    addRouters(app)

    # 6️⃣ Global exception mapping
    addGlobalExceptionHandlers(app)
    
    return app

# -------------------------
# ASGI entrypoint
# -------------------------

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


# http://127.0.0.1:8000/
