from openai import AsyncOpenAI
import httpx
from redis.asyncio import Redis
from app.application.ai.core.chat_pipeline import ChatPipeline
from app.application.ai.core.summarization_pipeline import SummarizationPipeline
from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_inference_port import AIInferencePort
from app.application.ai.domain.ai_provider import AIProvider
from app.application.ai.infrastructure.ai_inference_port import InferenceRouter
from app.application.ai.infrastructure.redis_ai_cache import RedisAIResponseCache
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
from app.core.config import Settings
from app.core.model_registry import ModelRegistry
from app.domain.exceptions.exceptions import ServiceError
from app.application.ai.core.circuit_breakers import CircuitBreaker
from app.application.ai.core.pipeline_registry import PipelineRegistry


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

        self.ollama_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=20,
        )
        self.openai_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
        )

        self.openai_adapter = OpenAIAdapter(
            self.openai_client, self.ai_settings, self.openai_breaker
        )
        self.ollama_adapter = OllamaAdapter(
            self.ollama_client, self.ai_settings, self.ollama_breaker
        )
        # -------------------------
        # AI Response Componenets
        # -------------------------
        self.prompt_evaluator = PromptEvaluator()
        self.guardrails = AIGuardrails(self.ai_settings)
        self.summary_prompt = SummaryPrompt()
        self.bullet_parser = BulletParser()
        self.safety_filter = AISafetyFilter()
        # -------------------------
        # Registry + Router
        # -------------------------

        self.model_registry = ModelRegistry(settings.ai)
        self.model_registry.register_adapter(AIProvider.OPENAI, self.openai_adapter)
        self.model_registry.register_adapter(AIProvider.OLLAMA, self.ollama_adapter)

        self.pipeline_registry = PipelineRegistry()

        self.pipeline_registry.register(AICapability.SUMMARIZATION,
                                        SummarizationPipeline(
                                            hallucination_guard=HallucinationGuard(),
                                            validator=AIResponseValidator(),
                                            scorer=AIResponseScorer(),
                                            parser=BulletParser(),
                                        ))
        self.pipeline_registry.register(AICapability.CHAT,
                                        ChatPipeline(
                                            validator=AIResponseValidator(),
                                            scorer=AIResponseScorer(),
                                        ))
        # -------------------------
        # AI Validation
        # -------------------------
        self.reliability_pipeline = SummarizationPipeline(
            hallucination_guard=HallucinationGuard(),
            validator=AIResponseValidator(),
            scorer=AIResponseScorer(),
            parser=self.bullet_parser,
        )

        self.router = InferenceRouter(
            registry=self.model_registry
        )

        self.redis = Redis(
            host="redis",  # docker service name
            port=6379,
            decode_responses=True,
        )

        self.ai_cache = RedisAIResponseCache(self.redis)

    def get_ai_inference(self) -> AIInferencePort:
        # Example strategy:
        # cheap local first → smart cloud fallback
        return self.router

    # 🔥 IMPORTANT
    async def startup(self):
        await self.model_registry.load()

    async def shutdown(self):
        await self.ollama_client.aclose()
        await self.model_registry.close()
        await self.redis.close()
