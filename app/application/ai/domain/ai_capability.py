from enum import Enum


class AICapability(str, Enum):
    SUMMARIZATION = "summarization"
    CHAT = "chat"
    EMBEDDING = "embedding"