import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_context import request_id_ctx


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1️⃣ Use incoming request ID if present (gateway / proxy support)
        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )

        # 2️⃣ Store request_id in context
        token = request_id_ctx.set(request_id)

        try:
            # 3️⃣ Process request
            response = await call_next(request)

            # 4️⃣ Expose request_id in response
            response.headers["X-Request-ID"] = request_id
            return response

        finally:
            # 5️⃣ Clean up context (CRITICAL)
            request_id_ctx.reset(token)
