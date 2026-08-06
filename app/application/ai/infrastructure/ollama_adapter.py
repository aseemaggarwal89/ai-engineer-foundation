import time
import logging
from typing import Optional

import httpx

from app.application.ai.core.circuit_breakers import CircuitBreaker
from app.core.config import AISettings
from app.core.retry import infra_retry
from app.application.ai.domain.ai_model_port import AIModelPort
from app.domain.exceptions.exceptions import AIProviderError, ProviderErrorCategory

logger = logging.getLogger(__name__)


class OllamaAdapter(AIModelPort):
    """
    Ollama implementation of AIModelPort.

    The rest of the application sees the same generate() contract as OpenAI,
    while this adapter handles Ollama's local HTTP API details.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        ai_settings: AISettings,
        breaker: CircuitBreaker,
    ):
        self.client = client
        self.settings = ai_settings
        self.provider = "ollama"
        self.breaker = breaker

    @infra_retry()
    # @tracer.traced("ai.generate")
    async def generate(
        self,
        *,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        # Avoid repeated local-model calls while Ollama is unhealthy.
        if not self.breaker.allow_request():
            logger.warning(
                "ai_circuit_prevented_request",
                extra={"provider": self.provider},
            )
            raise AIProviderError(
                "Ollama circuit open",
                category=ProviderErrorCategory.CIRCUIT_OPEN,
                provider=self.provider,
                model=self.settings.model_name,
            )
        try:
            result = await self._generate(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
            self.breaker.record_success()
            return result

        except AIProviderError as exc:
            if exc.fallback_eligible:
                self.breaker.record_failure()
            raise
        except Exception:
            self.breaker.record_failure()
            raise

    async def _generate(
        self,
        *,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:

        model = self.settings.model_name
        if not model:
            raise AIProviderError(
                "Ollama model is not configured",
                category=ProviderErrorCategory.CONFIGURATION,
                provider=self.provider,
                fallback_eligible=False,
            )

        start = time.perf_counter()

        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        try:
            logger.info(
                "ai_inference_started",
                extra={
                    "provider": self.provider,
                    "model": model,
                    "prompt_chars": len(prompt),
                },
            )

            response = await self.client.post(
                "/api/generate",
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            latency = time.perf_counter() - start

            logger.info(
                "ai_inference_completed",
                extra={
                    "provider": self.provider,
                    "model": model,
                    "latency_seconds": latency,
                },
            )

            # Ollama returns generated text in the "response" field.
            output_text: Optional[str] = data.get("response")

            if not output_text:
                logger.error(
                    "ai_empty_response",
                    extra={
                        "provider": self.provider,
                        "model": model,
                        "response_data": output_text,
                    },
                )

                raise AIProviderError(
                    "AI model returned empty response",
                    category=ProviderErrorCategory.INVALID_RESPONSE,
                    provider=self.provider,
                    model=model,
                )

            return output_text.strip()

        # Normalize transport/provider failures so router fallback remains simple.
        except httpx.TimeoutException as exc:
            logger.exception(
                "ai_timeout",
                extra={"provider": self.provider, "model": model},
            )

            raise AIProviderError(
                "AI provider timeout",
                category=ProviderErrorCategory.TIMEOUT,
                provider=self.provider,
                model=model,
            ) from exc

        except httpx.HTTPStatusError as exc:
            category = self._category_for_status(exc.response.status_code)
            logger.exception(
                "ai_provider_error",
                extra={
                    "provider": self.provider,
                    "model": model,
                    "status_code": exc.response.status_code,
                    "category": category.value,
                },
            )

            raise AIProviderError(
                "AI provider failure",
                category=category,
                provider=self.provider,
                model=model,
            ) from exc

        except httpx.HTTPError as exc:
            logger.exception(
                "ai_transport_error",
                extra={"provider": self.provider, "model": model},
            )

            raise AIProviderError(
                "AI transport failure",
                category=ProviderErrorCategory.NETWORK,
                provider=self.provider,
                model=model,
            ) from exc

        except AIProviderError:
            raise

        except Exception as exc:
            logger.exception(
                "ai_unknown_failure",
                extra={
                    "provider": self.provider,
                    "model": model,
                    "error": str(exc),
                },
            )

            raise AIProviderError(
                "AI inference failed",
                category=ProviderErrorCategory.UNKNOWN,
                provider=self.provider,
                model=model,
            ) from exc

    @staticmethod
    def _category_for_status(status_code: int) -> ProviderErrorCategory:
        if status_code in {401, 403}:
            return ProviderErrorCategory.AUTHENTICATION
        if status_code in {400, 404, 422}:
            return ProviderErrorCategory.INVALID_REQUEST
        if status_code == 408:
            return ProviderErrorCategory.TIMEOUT
        if status_code == 429:
            return ProviderErrorCategory.RATE_LIMIT
        if status_code >= 500:
            return ProviderErrorCategory.UNAVAILABLE
        return ProviderErrorCategory.UNKNOWN
