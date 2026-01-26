from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load .env into environment variables (only once at import time)
load_dotenv()


class Settings(BaseModel):
    # --------------------
    # App
    # --------------------
    app_name: str
    environment: str
    log_level: str

    # --------------------
    # Database
    # --------------------
    database_url: str

    # --------------------
    # JWT / Authentication
    # --------------------
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int


def get_settings() -> Settings:
    return Settings(
        # App
        app_name=os.getenv("APP_NAME", "AI Engineer Foundation"),
        environment=os.getenv("ENVIRONMENT", "local"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),

        # Database
        database_url=os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./app.db",
        ),

        # JWT
        jwt_secret_key=os.getenv(
            "JWT_SECRET_KEY",
            "CHANGE_ME_IN_PRODUCTION",
        ),
        jwt_algorithm=os.getenv(
            "JWT_ALGORITHM",
            "HS256",
        ),
        jwt_access_token_expire_minutes=int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        ),
    )
# Why this is correct

# load_dotenv() runs once

# .env → OS environment

# os.getenv() reads from OS

# BaseModel validates
