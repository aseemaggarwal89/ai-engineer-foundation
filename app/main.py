# flake8: noqa

import sys
from pathlib import Path

from app.application.ai.core.container import ServiceContainer
from app.core.middleware.body_size import BodySizeLimitMiddleware
from app.core.middleware.metrics_middleware import MetricsMiddleware

# Keep the project root importable when running the module directly.
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
from app.core.middleware.request_id import RequestIDMiddleware

from app.core.tracing import setup_tracing

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup creates long-lived resources once per process. Request handlers
    # reuse this AI container through app.state.container.
    logger.info("Application startup")
    settings = get_settings()
    container = ServiceContainer(settings)
    await container.startup()
    app.state.container = container

    logging.getLogger(__name__).info("Initializing database")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Application runs here

    # Shutdown closes long-lived network clients cleanly.
    await container.shutdown()
    logger.info("Application shutdown")

    
def create_app() -> FastAPI:
    settings = get_settings()

    # Logging first so startup, tracing, middleware, and routes share one format.
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

    # FastAPI owns the lifespan hook where the AI container is initialized.
    app = FastAPI(
        title=settings.app_name,
        debug=settings.environment == "local",
        lifespan=lifespan,
    )

    # Tracing is optional for local runs and enabled when an OTLP endpoint exists.
    if settings.ai.otlp_endpoint:
        setup_tracing(app, settings.app_name, settings.ai.otlp_endpoint)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # Metrics and request IDs wrap every request before route handlers run.
    app.add_middleware(MetricsMiddleware)

    app.add_middleware(RequestIDMiddleware)

    app.add_middleware(
    BodySizeLimitMiddleware,
    max_body_size=settings.ai.max_request_bytes,
    )
    
    addRouters(app)

    # Domain exceptions become consistent HTTP JSON responses here.
    addGlobalExceptionHandlers(app)
    
    return app

# -------------------------
# ASGI entrypoint
# -------------------------

# Uvicorn imports this ASGI app.
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
