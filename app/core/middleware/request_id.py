import uuid
import re
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_context import request_id_ctx


REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1️⃣ Reuse bounded gateway/proxy IDs only when they are safe for logs.
        request_id = self._request_id_or_new(request.headers.get("X-Request-ID"))

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

    @staticmethod
    def _request_id_or_new(value: str | None) -> str:
        if value and REQUEST_ID_PATTERN.fullmatch(value.strip()):
            return value.strip()

        return str(uuid.uuid4())
