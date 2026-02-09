from openai import AsyncOpenAI
import httpx

from app.application.ai.core.ai_reliability_pipeline import AIReliabilityPipeline
from app.application.ai.validator.prompt_evaluator import PromptEvaluator
from app.application.ai.validator.request.ai_guardrails import AIGuardrails
from app.application.ai.core.bullet_parser import BulletParser
from app.application.ai.domain.ai_model_port import AIModelPort
from app.application.ai.infrastructure.ollama_adapter import OllamaAdapter
from app.application.ai.infrastructure.openai_adapter import OpenAIAdapter
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.application.ai.validator.response.hallucination_guard import HallucinationGuard
from app.application.ai.validator.request.ai_safety import AISafetyFilter
from app.application.ai.validator.response.response_scorer import AIResponseScorer
from app.application.ai.validator.response.response_validator import AIResponseValidator
from app.core.config import AIProvider, Settings
from app.core.model_registry import ModelRegistry
from app.domain.exceptions.exceptions import ServiceError


class ServiceContainer:
    """
    Owns ALL long-lived resources.

    Created once per process.
    Destroyed on shutdown.
    """

    def __init__(self, settings: Settings):

        self.ai_settings = settings.ai

        # -------------------------
        # Clients
        # -------------------------

        self.openai_client = AsyncOpenAI(
            api_key=self.ai_settings.openai_api_key,
            timeout=self.ai_settings.timeout_seconds,
        )

        self.ollama_client = httpx.AsyncClient(
            base_url=self.ai_settings.ollama_base_url,
            timeout=self.ai_settings.timeout_seconds,
        )

        # -------------------------
        # AI Response Componenets
        # -------------------------
        self.prompt_evaluator = PromptEvaluator()
        self.guardrails = AIGuardrails(self.ai_settings)
        self.summary_prompt = SummaryPrompt()
        self.bullet_parser = BulletParser()

        # -------------------------
        # Registry + Router
        # -------------------------

        self.model_registry = ModelRegistry(settings)

        # -------------------------
        # AI Validation
        # -------------------------

        self.reliability_pipeline = AIReliabilityPipeline(
            safety=AISafetyFilter(),
            hallucination_guard=HallucinationGuard(),
            validator=AIResponseValidator(),
            scorer=AIResponseScorer(),
        )
    
    def get_ai_model(self) -> AIModelPort:
        if self.ai_settings.provider == AIProvider.OPENAI:
            return OpenAIAdapter(
                self.openai_client,
                self.ai_settings,
            )
        if self.ai_settings.provider == AIProvider.OLLAMA:
            return OllamaAdapter(
                self.ollama_client,
                self.ai_settings,
            )
        raise ServiceError("Unsupported AI provider")

    # 🔥 IMPORTANT
    async def startup(self):
        await self.model_registry.load()

    async def shutdown(self):
        await self.ollama_client.aclose()
        await self.model_registry.close()