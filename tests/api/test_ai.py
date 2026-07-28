from fastapi.testclient import TestClient

from app.dependencies.ai_dependencies import get_summarize_use_case
from app.main import create_app


class FakeSummarizeUseCase:
    def __init__(self):
        self.received_text = None

    async def execute(self, text: str) -> list[str]:
        self.received_text = text
        return ["summary bullet"]


def test_summarize_route_awaits_use_case_and_returns_schema():
    app = create_app()
    use_case = FakeSummarizeUseCase()
    app.dependency_overrides[get_summarize_use_case] = lambda: use_case
    client = TestClient(app)

    response = client.post("/ai/summarize", json={"text": "Explain async FastAPI"})

    assert response.status_code == 200
    assert response.json() == {"bullets": ["summary bullet"]}
    assert use_case.received_text == "Explain async FastAPI"

    app.dependency_overrides.clear()


def test_summarize_route_rejects_blank_text_before_use_case():
    app = create_app()
    use_case = FakeSummarizeUseCase()
    app.dependency_overrides[get_summarize_use_case] = lambda: use_case
    client = TestClient(app)

    response = client.post("/ai/summarize", json={"text": "   "})

    assert response.status_code == 422
    assert use_case.received_text is None

    app.dependency_overrides.clear()


def test_summarize_route_rejects_text_over_hard_prompt_limit():
    app = create_app()
    use_case = FakeSummarizeUseCase()
    app.dependency_overrides[get_summarize_use_case] = lambda: use_case
    client = TestClient(app)

    response = client.post("/ai/summarize", json={"text": "x" * 20_001})

    assert response.status_code == 422
    assert use_case.received_text is None

    app.dependency_overrides.clear()
