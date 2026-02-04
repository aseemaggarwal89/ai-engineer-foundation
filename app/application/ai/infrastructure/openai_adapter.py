import time
import logging
from typing import Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from app.core import timeout, tracer
from app.core.config import AISettings
from app.core.retry import infra_retry
from app.dependencies.deps import settings
from app.application.ai.domain.ai_model_port import AIModelPort
from app.domain.exceptions.exceptions import ServiceError

logger = logging.getLogger(__name__)
cfg = settings()


class OpenAIAdapter(AIModelPort):

    def __init__(self, client: AsyncOpenAI, settings: AISettings):
        self.client = client
        self.settings = settings
        self.provider = "openai"

    @infra_retry()
    @tracer.traced("ai.generate")
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float,
        max_tokens: int
    ) -> str:

        model = self.settings.model_name
        start = time.perf_counter()

        try:
            logger.info(
                "ai_inference_started",
                extra={
                    "provider": self.provider,
                    "model": model,
                    "prompt_chars": len(prompt),
                },
            )

            response = await self.client.responses.create(
                model=model,
                input=prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            latency = time.perf_counter() - start

            logger.info(
                "ai_inference_completed",
                extra={
                    "provider": self.provider,
                    "model": model,
                    "latency_seconds": latency,
                },
            )

            # -----------------------------
            # Defensive Output Extraction
            # -----------------------------
            output_text: Optional[str] = getattr(response, "output_text", None)

            if not output_text:
                logger.error(
                    "ai_empty_response",
                    extra={
                        "provider": self.provider,
                        "model": model,
                    },
                )

                raise ServiceError("AI model returned empty response")

            return output_text

        # -----------------------------
        # Provider Failures → Normalize
        # -----------------------------

        except RateLimitError as exc:
            logger.exception(
                "ai_rate_limited",
                extra={"provider": self.provider, "model": model},
            )

            raise ServiceError(
                "AI provider rate limit exceeded"
            ) from exc

        except APITimeoutError as exc:
            logger.exception(
                "ai_timeout",
                extra={"provider": self.provider, "model": model},
            )

            raise ServiceError(
                "AI provider timeout"
            ) from exc

        except APIError as exc:
            logger.exception(
                "ai_provider_error",
                extra={"provider": self.provider, "model": model},
            )

            raise ServiceError(
                "AI provider failure"
            ) from exc

        except Exception as exc:
            logger.exception(
            "ai_unknown_failure",
            extra={
                "provider": self.provider,
                "model": model,
                "error": str(exc),   # 🔥 critical
            },
            )
            raise ServiceError(
                "AI inference failed"
            ) from exc