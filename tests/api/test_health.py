from fastapi.testclient import TestClient

from app.dependencies.use_cases import (
    get_deep_health_usecase,
    get_liveness_usecase,
    get_readiness_usecase,
)
from app.main import create_app


class FakeLivenessUseCase:
    async def execute(self):
        return {"status": "alive"}


class FakeReadinessUseCase:
    async def execute(self):
        return {"status": "ready"}


class FakeDeepHealthUseCase:
    async def execute(self):
        return {"database": "ok", "service": "ok"}


def test_health_root_returns_service_message():
    app = create_app()
    client = TestClient(app)

    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI service is running"}


def test_liveness_endpoint_returns_alive():
    app = create_app()
    app.dependency_overrides[get_liveness_usecase] = lambda: FakeLivenessUseCase()
    client = TestClient(app)

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

    app.dependency_overrides.clear()


def test_readiness_endpoint_uses_use_case():
    app = create_app()
    app.dependency_overrides[get_readiness_usecase] = lambda: FakeReadinessUseCase()
    client = TestClient(app)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

    app.dependency_overrides.clear()


def test_deep_health_endpoint_uses_use_case():
    app = create_app()
    app.dependency_overrides[get_deep_health_usecase] = lambda: FakeDeepHealthUseCase()
    client = TestClient(app)

    response = client.get("/health/deep")

    assert response.status_code == 200
    assert response.json() == {"database": "ok", "service": "ok"}

    app.dependency_overrides.clear()
