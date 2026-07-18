from enum import Enum
from functools import lru_cache
from pydantic import BaseModel, model_validator

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

    # Tracing
    otlp_endpoint: str | None = None
    
    # Common
    temperature: float = 0.6
    max_tokens: int = 512
    timeout_seconds: int = 40
    model_registry: ModelRegistrySettings | None = None
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
            route
            and (
                route.primary == AIProvider.OPENAI
                or route.fallback == AIProvider.OPENAI
            )
            for route in routes
        )

    def _valid_openai_key(self) -> bool:
        return bool(
            self.openai_api_key
            and self.openai_api_key.startswith("sk-")
            and self.openai_api_key != "your_openai_api_key_here"
        )

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
