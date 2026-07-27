from fastapi import Depends, Request
from app.application.ai.core.container import ServiceContainer
from app.application.ai.services.summary_service import SummaryService
from app.application.ai.usecases.summarize_text import SummarizeTextUseCase


def get_container(request: Request) -> ServiceContainer:
    """
    Fetch the AI container created once during FastAPI lifespan startup.

    This is the bridge from request-scoped FastAPI dependencies to reusable
    AI infrastructure such as provider clients, Redis, registries, and pipelines.
    """
    return request.app.state.container


def get_summary_service(
    container: ServiceContainer = Depends(get_container),
) -> SummaryService:
    """
    Build the summarization service from reusable container components.

    SummaryService is request-scoped, but its expensive dependencies are not.
    """
    return SummaryService(
        prompt=container.summary_prompt,
        inference=container.get_ai_inference(),
        cache=container.ai_cache,
        settings=container.ai_settings,
        pipeline_registry=container.pipeline_registry,
    )


def get_summarize_use_case(
    svc: SummaryService = Depends(get_summary_service),
    container: ServiceContainer = Depends(get_container),
) -> SummarizeTextUseCase:
    """
    Wire the application use case that the HTTP route calls.

    The use case receives request validators plus the AI orchestration service.
    """
    return SummarizeTextUseCase(
        guardrails=container.guardrails,
        safety=container.safety_filter,
        summary_service=svc,
        ai_settings=container.ai_settings,
    )
