from functools import lru_cache
from pydantic import BaseModel
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env into environment variables (only once at import time)
# load_dotenv()


class AISettings(BaseModel):
    openai_api_key: str
    model_name: str = "gpt-4.1"
    temperature: float = 0.2
    max_tokens: int = 512
    ai_timeout_seconds: int = 20


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
    environment: str = "local"
    log_level: str = "INFO"

    # --------------------
    # Database
    # --------------------
    database_url: str

    # --------------------
    # JWT
    # --------------------
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    db_timeout_seconds: int = 3
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
