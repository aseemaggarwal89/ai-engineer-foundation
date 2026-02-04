from fastapi import Depends
from openai import AsyncOpenAI
import httpx
from app.application.ai.core.ai_guardrails import AIGuardrails
from app.application.ai.core.bullet_parser import BulletParser
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.application.ai.services.summary_service import SummaryService
from app.application.ai.usecases.summarize_text import SummarizeTextUseCase
from app.core.config import AISettings, Settings, get_settings, AIProvider
from app.application.ai.infrastructure.openai_adapter import OpenAIAdapter
from app.application.ai.infrastructure.ollama_adapter import OllamaAdapter


def get_ai_settings(
    settings: Settings = Depends(get_settings),
) -> AISettings:
    return settings.ai


def get_open_ai_model(
    ai_settings: AISettings = Depends(get_ai_settings),
) -> OpenAIAdapter:
    client = AsyncOpenAI(
        api_key=ai_settings.openai_api_key,
        timeout=ai_settings.timeout_seconds,  # VERY important
    )

    return OpenAIAdapter(client, ai_settings)


def get_ollama_ai_model(
        ai_settings: AISettings = Depends(get_ai_settings),
) -> OllamaAdapter:
    client = httpx.AsyncClient(
        base_url=ai_settings.ollama_base_url,
        timeout=ai_settings.timeout_seconds,
    )

    return OllamaAdapter(client, ai_settings)


def get_ai_model(
    ai_settings: AISettings = Depends(get_ai_settings),
    ollama: OllamaAdapter = Depends(get_ollama_ai_model),
    open_ai: OpenAIAdapter = Depends(get_open_ai_model),
):
    if ai_settings.provider == AIProvider.OPENAI:
        return open_ai

    if ai_settings.provider == AIProvider.OLLAMA:
        return ollama

    raise ValueError("Unsupported AI provider")


def get_summary_service(
    model=Depends(get_ai_model),
    ai_settings: AISettings = Depends(get_ai_settings),
) -> SummaryService:
    return SummaryService(
        model=model,
        prompt=SummaryPrompt(),
        parser=BulletParser(),
        settings=ai_settings
    )


def get_summarize_use_case(
    svc: SummaryService = Depends(get_summary_service),
    ai_settings: AISettings = Depends(get_ai_settings),
) -> SummarizeTextUseCase:
    ai_guard: AIGuardrails = AIGuardrails(ai_settings)
    return SummarizeTextUseCase(ai_guard, svc)