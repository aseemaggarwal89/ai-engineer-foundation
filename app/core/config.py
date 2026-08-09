import math
from enum import Enum
from functools import lru_cache
from pydantic import BaseModel, Field, field_validator, model_validator

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.application.ai.domain.ai_provider import AIProvider
from app.application.ai.domain.model_registry import ModelRegistrySettings
from app.domain.exceptions.exceptions import ServiceError
# from dotenv import load_dotenv
# import os
# Load .env into environment variables (only once at import time)
# load_dotenv()

# =========================================================
# Environment Enum (Fail Fast)
# =========================================================


class Environment(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PROD = "prod"


class EmbeddingProvider(str, Enum):
    OPENAI = "openai"


class VectorStoreProvider(str, Enum):
    QDRANT = "qdrant"


class EmbeddingSettings(BaseModel):
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI
    model: str = "text-embedding-3-small"
    batch_size: int = 64
    timeout_seconds: int = 30

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("embedding model is required")
        return value

    @model_validator(mode="after")
    def validate_embedding_settings(self):
        if self.batch_size <= 0:
            raise ValueError("embedding batch_size must be greater than zero")

        if self.timeout_seconds <= 0:
            raise ValueError("embedding timeout_seconds must be greater than zero")

        return self


class VectorStoreSettings(BaseModel):
    provider: VectorStoreProvider = VectorStoreProvider.QDRANT
    url: str = "http://qdrant:6333"
    collection: str = "documents"
    timeout_seconds: int = 10

    @field_validator("url", "collection")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("vector-store text settings must not be empty")
        return value

    @model_validator(mode="after")
    def validate_vector_store_settings(self):
        if self.timeout_seconds <= 0:
            raise ValueError("vector-store timeout_seconds must be greater than zero")

        return self


class RAGSettings(BaseModel):
    enabled: bool = False
    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_top_k: int = 5
    minimum_score: float = 0.3
    max_document_bytes: int = 5 * 1024 * 1024
    max_chunks_per_document: int = 1000
    prompt_version: str = "v1"
    index_version: str = "v1"
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)

    @field_validator("prompt_version", "index_version")
    @classmethod
    def validate_version_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("RAG version settings must not be empty")
        return value

    @model_validator(mode="after")
    def validate_rag_settings(self):
        if self.chunk_size <= 0:
            raise ValueError("rag chunk_size must be greater than zero")

        if self.chunk_overlap < 0:
            raise ValueError("rag chunk_overlap must be greater than or equal to zero")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("rag chunk_overlap must be smaller than chunk_size")

        if self.retrieval_top_k <= 0:
            raise ValueError("rag retrieval_top_k must be greater than zero")

        if not math.isfinite(self.minimum_score):
            raise ValueError("rag minimum_score must be finite")

        if self.max_document_bytes <= 0:
            raise ValueError("rag max_document_bytes must be greater than zero")

        if self.max_chunks_per_document <= 0:
            raise ValueError("rag max_chunks_per_document must be greater than zero")

        return self
# =========================================================
# AI Settings
# =========================================================
    

class AISettings(BaseModel):
    provider: AIProvider = AIProvider.OLLAMA

    # OpenAI
    openai_api_key: str | None = None
    model_name: str | None = None

    # Ollama
    ollama_base_url: str = "http://ollama:11434"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    cache_namespace: str = "local"
    cache_ttl_seconds: int = 3600

    # Tracing
    otlp_endpoint: str | None = None
    
    # Common
    temperature: float = 0.6
    max_tokens: int = 512
    timeout_seconds: int = 40
    model_registry: ModelRegistrySettings | None = None
    rag: RAGSettings = Field(default_factory=RAGSettings)
    # Guardrails
    max_input_chars: int = 10_000
    hard_reject_chars: int = 50_000
    max_prompt_length: int = 8_000
    hard_prompt_limit: int = 20_000

    # Transport guardrail
    max_request_bytes: int = 262_144  # 256 KB
    
    # -----------------------------
    # Smart Defaults
    # -----------------------------

    @model_validator(mode="after")
    def validate_ai_settings(self):
        if self.model_name != self.provider.get_model_name():
            self.model_name = self.provider.get_model_name()

        if self._uses_openai() and not self._valid_openai_key():
            raise ServiceError("OPENAI API key is required when OpenAI is configured")

        return self

    def _uses_openai(self) -> bool:
        if self.provider == AIProvider.OPENAI:
            return True

        if not self.model_registry:
            return False

        routes = [
            self.model_registry.summarization,
            self.model_registry.chat,
        ]

        return any(
            self._route_uses_openai(route)
            for route in routes
        )

    @staticmethod
    def _route_uses_openai(route) -> bool:
        if not route:
            return False

        return route.primary == AIProvider.OPENAI or route.fallback == AIProvider.OPENAI

    def _valid_openai_key(self) -> bool:
        if not self.openai_api_key:
            return False

        is_placeholder = self.openai_api_key == "your_openai_api_key_here"
        return self.openai_api_key.startswith("sk-") and not is_placeholder

# =========================================================
# Root Settings
# =========================================================


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",   # Enables AI__ mapping
        extra="ignore"
    )

    # --------------------
    # App
    # --------------------
    app_name: str = "AI Engineer"
    environment: Environment = Environment.LOCAL
    log_level: str = "INFO"
    auto_create_tables: bool = False

    # --------------------
    # Database
    # --------------------
    database_url: str
    db_timeout_seconds: int = 3

    # --------------------
    # JWT
    # --------------------
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # --------------------
    # Rate Limits
    # --------------------
    login_rate_limit: str = "5/minute"

    # --------------------
    # Nested AI config
    # --------------------
    ai: AISettings


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    Loads once per process → critical for performance.
    """
    return Settings()

# Why this is correct
# load_dotenv() runs once

# .env → OS environment

# os.getenv() reads from OS

# BaseModel validates
