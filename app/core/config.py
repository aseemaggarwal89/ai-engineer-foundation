from enum import Enum
from functools import lru_cache
from pydantic import BaseModel, field_validator, model_validator

from pydantic_settings import BaseSettings, SettingsConfigDict
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
# AI Provider Enum
# =========================================================


class AIProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"

    def get_model_name(self) -> str:
        if self == AIProvider.OPENAI:
            return "gpt-4.1-mini"
        elif self == AIProvider.OLLAMA:
            return "tinyllama"
        else:
            raise ValueError("Unsupported AI provider")

# =========================================================
# AI Settings
# =========================================================
    

class AISettings(BaseModel):
    provider: AIProvider = AIProvider.OLLAMA

    # OpenAI
    openai_api_key: str | None = "your_openai_api_key_here__"
    model_name: str | None = None

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    
    # Common
    temperature: float = 0.6
    max_tokens: int = 512
    timeout_seconds: int = 20
    max_input_chars: int = 10_000
    hard_reject_chars: int = 50_000

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
    def set_model_name(self):
        if self.model_name != self.provider.get_model_name():
            self.model_name = self.provider.get_model_name()

        return self
    
    # -----------------------------
    # Validation
    # -----------------------------
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not v or v == "your_openai_api_key_here":
            raise ValueError("OPENAI API key is not set")

        if not v.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")

        return v

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
