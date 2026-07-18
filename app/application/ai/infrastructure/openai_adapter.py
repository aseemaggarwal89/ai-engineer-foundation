import time
import logging
from typing import Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from app.core import tracer
from app.application.ai.core.circuit_breakers import CircuitBreaker
from app.core.config import AISettings
from app.core.retry import infra_retry
from app.application.ai.domain.ai_model_port import AIModelPort
from app.domain.exceptions.exceptions import AIProviderError

logger = logging.getLogger(__name__)


class OpenAIAdapter(AIModelPort):
    """
    OpenAI implementation of AIModelPort.

    The adapter translates the common application contract into OpenAI's API
    shape and normalizes vendor-specific failures into AIProviderError so the
    router can apply fallback consistently.
    """

    def __init__(
        self,
        client: AsyncOpenAI,
        ai_settings: AISettings,
        breaker: CircuitBreaker,
    ):
        self.client = client
        self.settings = ai_settings
        self.provider = "openai"
        self.breaker = breaker

    @infra_retry()
    @tracer.traced("ai.generate")
    async def generate(
        self,
        *,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        # Circuit breaker check happens before the retry wrapper spends time on
        # a provider that is already considered unhealthy.
        if not self.breaker.allow_request():
            logger.warning(
                "ai_circuit_prevented_request",
                extra={"provider": self.provider},
            )
            raise AIProviderError("OpenAI circuit open")
        
        try:
            result = await self._generate(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
            self.breaker.record_success()
            return result
        except Exception:
            self.breaker.record_failure()
            raise

    async def _generate(self, *, prompt: str, temperature: float, max_tokens: int) -> str:

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

            # Providers can return successful envelopes with empty content; keep
            # that failure inside the adapter contract.
            output_text: Optional[str] = getattr(response, "output_text", None)

            if not output_text:
                logger.error(
                    "ai_empty_response",
                    extra={
                        "provider": self.provider,
                        "model": model,
                    },
                )

                raise AIProviderError("AI model returned empty response")

            return output_text

        # Normalize provider failures so the router does not know OpenAI types.
        except RateLimitError as exc:
            logger.exception(
                "ai_rate_limited",
                extra={"provider": self.provider, "model": model},
            )

            raise AIProviderError("AI provider rate limit exceeded") from exc

        except APITimeoutError as exc:
            logger.exception(
                "ai_timeout",
                extra={"provider": self.provider, "model": model},
            )

            raise AIProviderError("AI provider timeout") from exc

        except APIError as exc:
            logger.exception(
                "ai_provider_error",
                extra={"provider": self.provider, "model": model},
            )

            raise AIProviderError("AI provider failure") from exc

        except Exception as exc:
            logger.exception(
                "ai_unknown_failure",
                extra={
                    "provider": self.provider,
                    "model": model,
                    "error": str(exc),
                },
            )
            raise AIProviderError("AI inference failed") from exc
