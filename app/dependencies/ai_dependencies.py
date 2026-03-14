from fastapi import Depends, Request
from app.application.ai.core.container import ServiceContainer
from app.application.ai.services.summary_service import SummaryService
from app.application.ai.usecases.summarize_text import SummarizeTextUseCase


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container


def get_summary_service(
    container: ServiceContainer = Depends(get_container),
) -> SummaryService:
    return SummaryService(
        prompt=container.summary_prompt,
        inference=container.get_ai_inference(),
        cache=container.ai_cache,
        settings=container.ai_settings,
        reliability_pipeline=container.reliability_pipeline,
    )


def get_summarize_use_case(
    svc: SummaryService = Depends(get_summary_service),
    container: ServiceContainer = Depends(get_container),
) -> SummarizeTextUseCase:
    return SummarizeTextUseCase(
        guardrails=container.guardrails,
        safety=container.safety_filter,
        summary_service=svc,
        ai_settings=container.ai_settings,
    )