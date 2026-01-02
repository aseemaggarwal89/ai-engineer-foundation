from fastapi.testclient import TestClient

from app.main import create_app
from app.dependencies.deps import health_service


class FakeHealthService:
    async def check(self) -> str:
        return "test-ok"


def get_fake_health_service():
    return FakeHealthService()


def test_health_endpoint_returns_ok():
    app = create_app()

    # Override dependency
    app.dependency_overrides[health_service] = get_fake_health_service

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "test-ok"}

    # Cleanup (important)
    app.dependency_overrides.clear()


def test_health_endpoint_uses_database(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Call again – data should come from DB, not reinsert
    response2 = client.get("/health")
    assert response2.status_code == 200
    assert response2.json() == {"status": "ok"}
