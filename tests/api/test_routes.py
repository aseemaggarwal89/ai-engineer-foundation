from uuid import uuid4

from fastapi.testclient import TestClient

from app.domain.entities.user import User
from app.domain.entities.user_role import UserRole
from app.domain.exceptions.exceptions import ServiceError
from app.dependencies.ai_dependencies import get_summarize_use_case
from app.main import create_app
from app.security.dependencies import get_current_active_user


def _route_index(app):
    return {
        (route.path, method): route
        for route in app.routes
        if hasattr(route, "methods")
        for method in route.methods
    }


def _fake_user(role: UserRole) -> User:
    return User(
        id=uuid4(),
        email="route-test@example.com",
        is_active=True,
        role=role,
    )


def test_expected_application_routes_are_registered():
    app = create_app()
    routes = _route_index(app)

    expected_routes = {
        ("/health/", "GET"),
        ("/health/live", "GET"),
        ("/health/ready", "GET"),
        ("/health/deep", "GET"),
        ("/health", "GET"),
        ("/metrics", "GET"),
        ("/auth/register", "POST"),
        ("/auth/login", "POST"),
        ("/auth/me", "GET"),
        ("/auth/users", "GET"),
        ("/admin/dashboard", "GET"),
        ("/ai/summarize", "POST"),
    }

    assert expected_routes.issubset(routes.keys())
    assert routes[("/ai/summarize", "POST")].tags == ["ai"]
    assert routes[("/auth/register", "POST")].tags == ["auth"]
    assert routes[("/admin/dashboard", "GET")].tags == ["admin"]


def test_public_routes_are_accessible_without_authentication():
    app = create_app()
    client = TestClient(app)

    assert client.get("/health/").status_code == 200
    assert client.get("/metrics").status_code == 200


def test_protected_routes_reject_missing_credentials():
    app = create_app()
    client = TestClient(app)

    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/users").status_code == 401
    assert client.get("/health").status_code == 401
    assert client.get("/admin/dashboard").status_code == 401


def test_admin_dashboard_rejects_authenticated_non_admin_user():
    app = create_app()
    app.dependency_overrides[get_current_active_user] = lambda: _fake_user(UserRole.USER)
    client = TestClient(app)

    response = client.get("/admin/dashboard")

    assert response.status_code == 403
    assert response.json() == {
        "error_code": "FORBIDDEN",
        "message": "Insufficient permissions",
    }

    app.dependency_overrides.clear()


def test_ai_route_validation_error_for_invalid_payload():
    app = create_app()
    app.dependency_overrides[get_summarize_use_case] = lambda: object()
    client = TestClient(app)

    response = client.post("/ai/summarize", json={"text": ""})

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_application_exception_is_mapped_by_global_handler():
    app = create_app()

    @app.get("/test-error")
    async def test_error():
        raise ServiceError("Route test failure")

    client = TestClient(app)

    response = client.get("/test-error")

    assert response.status_code == 500
    assert response.json() == {
        "error_code": "SERVICE_ERROR",
        "message": "Route test failure",
    }


def test_openapi_contains_expected_route_tags_and_security_scheme():
    app = create_app()
    client = TestClient(app)

    schema = client.get("/openapi.json").json()

    assert schema["paths"]["/ai/summarize"]["post"]["tags"] == ["ai"]
    assert schema["paths"]["/auth/register"]["post"]["tags"] == ["auth"]
    assert schema["paths"]["/admin/dashboard"]["get"]["tags"] == ["admin"]
    assert "JWT" in schema["components"]["securitySchemes"]
