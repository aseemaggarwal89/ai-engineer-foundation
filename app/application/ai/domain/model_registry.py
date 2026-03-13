from pydantic import BaseModel

from app.application.ai.domain.ai_provider import AIProvider


class ModelRoute(BaseModel):
    primary: AIProvider
    fallback: AIProvider | None = None


class ModelRegistrySettings(BaseModel):
    summarization: ModelRoute
    chat: ModelRoute | None = None