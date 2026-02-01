from app.core import tracer
import logging
from app.core.config import AISettings
from app.domain.ai.ai_model_port import AIModelPort

logger = logging.getLogger(__name__)


class OpenAIAdapter(AIModelPort):

    def __init__(self, client, settings: AISettings):
        self.client = client
        self.settings = settings

    @tracer.traced("ai.generate")
    async def generate(self, prompt, *, temperature, max_tokens):
        logger.info("ai_request", extra={"model": self.settings.model_name})

        resp = await self.client.responses.create(
            model=self.settings.model_name,
            input=prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        return resp.output_text
