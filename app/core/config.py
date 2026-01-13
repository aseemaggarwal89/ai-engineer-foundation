from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load .env into environment variables (only once at import time)
load_dotenv()


class Settings(BaseModel):
    app_name: str
    environment: str
    log_level: str


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AI Engineer Foundation"),
        environment=os.getenv("ENVIRONMENT", "local"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )

# Why this is correct

# load_dotenv() runs once

# .env → OS environment

# os.getenv() reads from OS

# BaseModel validates
