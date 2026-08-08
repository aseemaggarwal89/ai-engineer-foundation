import time
from starlette.routing import Match
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
        path = request.url.path
        start = time.perf_counter()
        status = 500  # ✅ default fallback for exceptions

        try:
            response = await call_next(request)
            status = response.status_code
            path = self._route_template(request)
            return response

        except Exception:
            path = self._route_template(request)
            REQUEST_ERRORS.labels(method, path).inc()
            raise

        finally:
            duration = time.perf_counter() - start

            REQUEST_COUNT.labels(method, path, status).inc()
            REQUEST_LATENCY.labels(method, path).observe(duration)

    @staticmethod
    def _route_template(request: Request) -> str:
        route = request.scope.get("route")
        if route and getattr(route, "path", None):
            return route.path

        router = request.scope.get("router")
        if router:
            for route in getattr(router, "routes", []):
                matches, _ = route.matches(request.scope)
                if matches == Match.FULL and getattr(route, "path", None):
                    return route.path

        return request.url.path
