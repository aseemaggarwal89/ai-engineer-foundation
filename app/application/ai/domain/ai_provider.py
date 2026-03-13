from enum import Enum
from app.domain.exceptions.exceptions import ServiceError


class AIProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"

    def get_model_name(self) -> str:
        if self == AIProvider.OPENAI:
            return "gpt-4.1-mini"
        elif self == AIProvider.OLLAMA:
            return "tinyllama"
        else:
            raise ServiceError("Unsupported AI provider")