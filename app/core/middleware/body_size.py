from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
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
            try:
                declared_size = int(content_length)
            except ValueError:
                return JSONResponse(
                    content={
                        "error_code": "INVALID_CONTENT_LENGTH",
                        "message": "Content-Length header must be a valid integer.",
                    },
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            if declared_size < 0:
                return JSONResponse(
                    content={
                        "error_code": "INVALID_CONTENT_LENGTH",
                        "message": "Content-Length header must be non-negative.",
                    },
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            if declared_size > self.max_body_size:
                return JSONResponse(
                    content={
                        "error_code": "REQUEST_TOO_LARGE",
                        "message": "Request body exceeds the allowed size.",
                    },
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                )

        return await call_next(request)
