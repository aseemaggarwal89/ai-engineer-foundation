from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette import status


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Reject requests exceeding configured size
    BEFORE FastAPI reads the body.
    """

    def __init__(self, app, max_body_size: int):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        
        # Reject early without reading body
        if content_length:
            if int(content_length) > self.max_body_size:
                return Response(
                    content="Request too large",
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                )

        return await call_next(request)
