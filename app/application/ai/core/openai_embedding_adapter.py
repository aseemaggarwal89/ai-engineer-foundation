from typing import List
from openai import AsyncOpenAI

from app.application.ai.domain.embedding_port import EmbeddingPort
from app.application.ai.core.circuit_breakers import CircuitBreaker
from app.core.retry import infra_retry
from app.core.config import AISettings
from app.domain.exceptions.exceptions import AIProviderError


class OpenAIEmbeddingAdapter(EmbeddingPort):

    def __init__(
        self,
        client: AsyncOpenAI,
        settings: AISettings,
        breaker: CircuitBreaker,
    ):
        self.client = client
        self.settings = settings
        self.breaker = breaker

    @infra_retry()
    async def embed(self, text: str) -> List[float]:
        if not self.breaker.allow_request():
            raise AIProviderError("OpenAI embedding circuit open")

        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            self.breaker.record_success()
            return response.data[0].embedding

        except Exception:
            self.breaker.record_failure()
            raise
