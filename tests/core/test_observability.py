import asyncio
import json
import logging
import re
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import JsonFormatter
from app.core.middleware.body_size import BodySizeLimitMiddleware
from app.core.middleware.metrics_middleware import MetricsMiddleware
from app.core.middleware.request_id import RequestIDMiddleware
from app.core.request_context import request_id_ctx
from app.core.tracer import traced


def test_json_formatter_includes_request_id_extra_fields_and_exception():
    formatter = JsonFormatter()
    token = request_id_ctx.set("req-test-1")
    try:
        try:
            raise ValueError("boom")
        except ValueError:
            record = logging.getLogger("test.logger").makeRecord(
                name="test.logger",
                level=logging.ERROR,
                fn=__file__,
                lno=1,
                msg="test message",
                args=(),
                exc_info=sys.exc_info(),
                extra={"custom": object()},
            )

        payload = json.loads(formatter.format(record))
    finally:
        request_id_ctx.reset(token)

    assert payload["level"] == "ERROR"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "test message"
    assert payload["request_id"] == "req-test-1"
    assert payload["custom"].startswith("<object object at")
    assert "ValueError: boom" in payload["exception"]


def test_request_id_middleware_reuses_bounded_safe_request_id():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    async def root():
        return {"request_id": request_id_ctx.get()}

    response = TestClient(app).get("/", headers={"X-Request-ID": "client-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "client-123"
    assert response.json() == {"request_id": "client-123"}
    assert request_id_ctx.get() is None


@pytest.mark.parametrize(
    "bad_request_id",
    [
        "x" * 129,
        "bad id with spaces",
        "bad\nid",
    ],
)
def test_request_id_middleware_replaces_invalid_client_request_id(bad_request_id):
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    async def root():
        return {"request_id": request_id_ctx.get()}

    response = TestClient(app).get("/", headers={"X-Request-ID": bad_request_id})

    assert response.status_code == 200
    generated = response.headers["X-Request-ID"]
    assert generated != bad_request_id
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        generated,
    )
    assert response.json() == {"request_id": generated}


def test_request_id_context_is_isolated_across_concurrent_requests():
    async def worker(value: str) -> str:
        token = request_id_ctx.set(value)
        try:
            await asyncio.sleep(0)
            return request_id_ctx.get()
        finally:
            request_id_ctx.reset(token)

    async def main():
        return await asyncio.gather(worker("req-a"), worker("req-b"))

    results = asyncio.run(main())

    assert results == ["req-a", "req-b"]
    assert request_id_ctx.get() is None


def test_body_size_middleware_rejects_oversized_declared_content_length():
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_body_size=3)

    @app.post("/")
    async def root():
        return {"ok": True}

    response = TestClient(app).post("/", content=b"abcd")

    assert response.status_code == 413
    assert response.json() == {
        "error_code": "REQUEST_TOO_LARGE",
        "message": "Request body exceeds the allowed size.",
    }


def test_metrics_middleware_uses_route_template_for_dynamic_path():
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)

    @app.get("/observability-test-items/{item_id}")
    async def get_item(item_id: str):
        return {"item_id": item_id}

    response = TestClient(app).get("/observability-test-items/123")

    assert response.status_code == 200
    metrics_text = generate_latest().decode()
    assert 'path="/observability-test-items/{item_id}"' in metrics_text
    assert 'path="/observability-test-items/123"' not in metrics_text


def test_middleware_effective_order_is_last_added_first_inbound():
    events: list[str] = []

    class RecordingMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, name: str):
            super().__init__(app)
            self.name = name

        async def dispatch(self, request, call_next):
            events.append(f"{self.name}:in")
            response = await call_next(request)
            events.append(f"{self.name}:out")
            return response

    app = FastAPI()
    app.add_middleware(RecordingMiddleware, name="first-added")
    app.add_middleware(RecordingMiddleware, name="second-added")

    @app.get("/")
    async def root():
        events.append("route")
        return {"ok": True}

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert events == [
        "second-added:in",
        "first-added:in",
        "route",
        "first-added:out",
        "second-added:out",
    ]


def test_traced_decorator_preserves_async_return_and_reraises_errors():
    @traced("test.success")
    async def succeeds():
        return "ok"

    @traced("test.failure")
    async def fails():
        raise RuntimeError("failed")

    assert asyncio.run(succeeds()) == "ok"

    with pytest.raises(RuntimeError, match="failed"):
        asyncio.run(fails())
