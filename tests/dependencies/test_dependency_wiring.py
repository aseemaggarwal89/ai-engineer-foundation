import inspect
from types import SimpleNamespace

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.application.ai.core.container import ServiceContainer
from app.application.ai.services.summary_service import SummaryService
from app.application.ai.usecases.summarize_text import SummarizeTextUseCase
from app.dependencies.ai_dependencies import get_summary_service, get_summarize_use_case
from app.dependencies.repositories import get_user_repository
from app.dependencies.use_cases import (
    get_current_user_use_case,
    get_list_users_use_case,
    get_login_user_use_case,
    get_register_user_use_case,
)
from app.domain.use_cases.user.get_current_user import GetCurrentUserUseCase
from app.domain.use_cases.user.list_users import ListUsersUseCase
from app.domain.use_cases.user.login_user import LoginUserUseCase
from app.domain.use_cases.user.register_user import RegisterUserUseCase
from app.repositories.user_repository import SQLAlchemyUserRepository


class FakeInference:
    pass


class FakeContainer:
    def __init__(self):
        self.summary_prompt = object()
        self.ai_cache = object()
        self.ai_settings = SimpleNamespace(
            model_name="tinyllama",
            temperature=0.6,
            max_tokens=512,
            timeout_seconds=40,
        )
        self.pipeline_registry = object()
        self.guardrails = object()
        self.safety_filter = object()
        self.inference = FakeInference()

    def get_ai_inference(self):
        return self.inference


def test_repository_provider_injects_request_scoped_session():
    session = object()
    settings = SimpleNamespace(db_timeout_seconds=3)

    repository = get_user_repository(session=session, settings=settings)

    assert isinstance(repository, SQLAlchemyUserRepository)
    assert repository._session is session
    assert repository.timeout_seconds == 3


def test_use_case_providers_construct_use_cases_from_repository_port():
    repository = object()

    assert isinstance(get_register_user_use_case(repository), RegisterUserUseCase)
    assert isinstance(get_login_user_use_case(repository), LoginUserUseCase)
    assert isinstance(get_current_user_use_case(repository), GetCurrentUserUseCase)
    assert isinstance(get_list_users_use_case(repository), ListUsersUseCase)


def test_ai_dependency_wiring_uses_container_only_in_dependency_layer():
    container = FakeContainer()

    service = get_summary_service(container)
    use_case = get_summarize_use_case(service, container)

    assert isinstance(service, SummaryService)
    assert service.prompt is container.summary_prompt
    assert service.inference is container.inference
    assert service.cache is container.ai_cache
    assert service.pipeline_registry is container.pipeline_registry
    assert isinstance(use_case, SummarizeTextUseCase)
    assert use_case.guardrails is container.guardrails
    assert use_case.safety is container.safety_filter
    assert use_case.summary_service is service


def test_use_cases_and_services_do_not_accept_service_container():
    classes = [
        RegisterUserUseCase,
        LoginUserUseCase,
        GetCurrentUserUseCase,
        ListUsersUseCase,
        SummaryService,
        SummarizeTextUseCase,
    ]

    for cls in classes:
        signature = inspect.signature(cls.__init__)
        annotations = {
            parameter.annotation
            for parameter in signature.parameters.values()
            if parameter.name != "self"
        }
        assert ServiceContainer not in annotations


def test_fastapi_caches_same_dependency_once_per_request():
    app = FastAPI()
    calls = {"count": 0}

    def dependency():
        calls["count"] += 1
        return {"call": calls["count"]}

    @app.get("/dependency-cache")
    def dependency_cache(
        first=Depends(dependency),
        second=Depends(dependency),
    ):
        return {
            "same_object": first is second,
            "first": first["call"],
            "second": second["call"],
        }

    client = TestClient(app)

    response = client.get("/dependency-cache")

    assert response.status_code == 200
    assert response.json() == {
        "same_object": True,
        "first": 1,
        "second": 1,
    }
    assert calls["count"] == 1
