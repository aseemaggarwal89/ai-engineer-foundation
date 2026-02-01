import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    REQUEST_ERRORS,
)


class MetricsMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        method = request.method
        route = request.scope.get("route")
        path = route.path if route else request.url.path
        start = time.perf_counter()
        status = 500  # ✅ default fallback for exceptions
        
        try:
            response = await call_next(request)
            status = response.status_code
            return response

        except Exception:
            REQUEST_ERRORS.labels(method, path).inc()
            raise

        finally:
            duration = time.perf_counter() - start

            REQUEST_COUNT.labels(method, path, status).inc()
            REQUEST_LATENCY.labels(method, path).observe(duration)
