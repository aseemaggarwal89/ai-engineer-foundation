import time
import logging
from typing import Optional

import httpx
import pybreaker

from app.core import timeout, tracer
from app.core.config import AISettings
from app.core.retry import infra_retry
from app.dependencies.deps import settings
from app.application.ai.domain.ai_model_port import AIModelPort
from app.domain.exceptions.exceptions import AIProviderError

logger = logging.getLogger(__name__)


class OllamaAdapter(AIModelPort):

    def __init__(self, client: httpx.AsyncClient, 
                 ai_settings: AISettings,
                 breaker: pybreaker.CircuitBreaker):
        self.client = client
        self.settings = ai_settings
        self.provider = "ollama"
        self.breaker = breaker

    @infra_retry()
    @tracer.traced("ai.generate")
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        try:
            return await self.breaker.call_async(
                self._generate,
                prompt,
                temperature,
                max_tokens,
            )

        except pybreaker.CircuitBreakerError:
            logger.warning(
                "ai_circuit_open",
                extra={"provider": self.provider},
            )
            raise AIProviderError("Ollama circuit open")
    
    async def _generate(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:

        model = self.settings.model_name
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

            # -----------------------------
            # Defensive Output Extraction
            # -----------------------------
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

                raise AIProviderError("AI model returned empty response")

            return output_text.strip()

        # -----------------------------
        # Normalize Failures
        # -----------------------------

        except httpx.TimeoutException as exc:
            logger.exception(
                "ai_timeout",
                extra={"provider": self.provider, "model": model},
            )

            raise AIProviderError(
                "AI provider timeout"
            ) from exc

        except httpx.HTTPStatusError as exc:
            logger.exception(
                "ai_provider_error",
                extra={
                    "provider": self.provider,
                    "model": model,
                    "status_code": exc.response.status_code,
                },
            )

            raise AIProviderError(
                "AI provider failure"
            ) from exc

        except httpx.HTTPError as exc:
            logger.exception(
                "ai_transport_error",
                extra={"provider": self.provider, "model": model},
            )

            raise AIProviderError(
                "AI transport failure"
            ) from exc

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
                "AI inference failed"
            ) from exc
