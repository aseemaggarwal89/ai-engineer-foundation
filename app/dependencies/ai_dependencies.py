from functools import lru_cache
from fastapi import Depends, Request
from openai import AsyncOpenAI
import httpx
from app.application.ai.core.ai_guardrails import AIGuardrails
from app.application.ai.core.bullet_parser import BulletParser
from app.application.ai.core.container import ServiceContainer
from app.application.ai.domain.ai_model_port import AIModelPort
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.application.ai.services.summary_service import SummaryService
from app.application.ai.usecases.summarize_text import SummarizeTextUseCase
from app.core.config import AISettings, Settings, get_settings, AIProvider
from app.application.ai.infrastructure.openai_adapter import OpenAIAdapter
from app.application.ai.infrastructure.ollama_adapter import OllamaAdapter
from app.domain.exceptions.exceptions import ServiceError


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container


def resolve_summary_model(
    container=Depends(get_container)
) -> AIModelPort:
    return container.get_ai_model()


def get_ai_settings(
    settings: Settings = Depends(get_settings),
) -> AISettings:
    return settings.ai


def get_summary_service(
    model=Depends(resolve_summary_model),
    ai_settings: AISettings = Depends(get_ai_settings),
) -> SummaryService:
    return SummaryService(
        model=model, prompt=SummaryPrompt(), parser=BulletParser(), settings=ai_settings
    )


def get_summarize_use_case(
    svc: SummaryService = Depends(get_summary_service),
    ai_settings: AISettings = Depends(get_ai_settings),
) -> SummarizeTextUseCase:
    ai_guard: AIGuardrails = AIGuardrails(ai_settings)
    return SummarizeTextUseCase(ai_guard, svc)
