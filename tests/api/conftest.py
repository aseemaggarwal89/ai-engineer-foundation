import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import get_db_session


@pytest.fixture
def client():
    app = create_app()

    async def override_get_db():
        yield get_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
