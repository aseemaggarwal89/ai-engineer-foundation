# 09 - Provider Abstraction: Ollama, OpenAI, Model Registry, and Inference Router

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


One of the most important AI backend concepts in this project is provider abstraction.

The application should not care whether the model response comes from:

- Ollama
- OpenAI
- another cloud model
- another local model

The application should only ask:

> I need text generated for this AI capability.

## Why Provider Abstraction Matters

If business logic directly calls Ollama, switching to OpenAI becomes difficult.

If business logic directly calls OpenAI, local development becomes harder.

Provider abstraction solves this.

It lets the application depend on an interface instead of a specific vendor.

## AIModelPort

The provider interface is:

```text
app/application/ai/domain/ai_model_port.py
```

It defines:

```python
async def generate(
    self,
    *,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    ...
```

Any provider that can generate text can implement this port.

## Ollama Adapter

The local provider implementation is:

```text
app/application/ai/infrastructure/ollama_adapter.py
```

Ollama is useful for local development because it lets you run models without depending on a cloud provider.

The adapter sends a request to:

```text
POST /api/generate
```

Inside Docker Compose, the app calls:

```text
http://ollama:11434
```

This teaches local AI development with a real model server.

## OpenAI Adapter

The cloud provider implementation is:

```text
app/application/ai/infrastructure/openai_adapter.py
```

The adapter uses the OpenAI client and returns generated text through the same `AIModelPort`.

The rest of the application does not need to know OpenAI-specific API details.

## Normalizing Errors

Ollama and OpenAI fail differently.

Ollama can fail with HTTP or network errors.

OpenAI can fail with:

- timeout
- rate limit
- API error

Both adapters normalize failures into:

```text
AIProviderError
```

This is important because fallback logic should not know vendor-specific exception classes.

## Model Registry

The model registry lives in:

```text
app/core/model_registry.py
```

It maps AI capabilities to providers.

Example:

```env
AI__MODEL_REGISTRY__SUMMARIZATION__PRIMARY=ollama
AI__MODEL_REGISTRY__SUMMARIZATION__FALLBACK=openai
```

This tells the app:

```text
For summarization:
  primary = Ollama
  fallback = OpenAI
```

## Capability-Based Routing

The project defines AI capabilities:

```text
app/application/ai/domain/ai_capability.py
```

Examples:

```python
SUMMARIZATION = "summarization"
CHAT = "chat"
EMBEDDING = "embedding"
```

This design is powerful because different capabilities may use different models.

For example:

```text
summarization -> local model
chat -> cloud model
embedding -> embedding model
rag -> retrieval-aware generation model
```

## Inference Router

The inference router lives in:

```text
app/application/ai/infrastructure/ai_inference_port.py
```

It does:

```text
get primary provider
-> try primary provider
-> if primary raises AIProviderError
-> try fallback provider
-> if fallback fails
-> raise service error
```

The service calls:

```python
await self.inference.generate(
    capability=AICapability.SUMMARIZATION,
    prompt=prompt_text,
    temperature=settings.temperature,
    max_tokens=settings.max_tokens,
)
```

Notice that the service asks for a capability, not a provider.

## Provider Fallback

Fallback improves reliability.

Example:

```text
Ollama is down
-> router catches AIProviderError
-> router calls OpenAI fallback
-> user still gets a response
```

This is useful for enterprise systems because provider availability can change.

## Circuit Breaker

Each provider has a circuit breaker:

```text
app/application/ai/core/circuit_breakers.py
```

If a provider fails repeatedly, the circuit opens and stops sending requests for a recovery window.

This avoids repeatedly hitting an unhealthy provider.

## Retry and Timeout

Provider calls also use retry and timeout patterns:

```text
app/core/retry.py
app/core/timeout.py
```

These protect the backend from temporary failures and long-running requests.

## Enterprise Lesson

This design separates responsibilities:

| Component | Responsibility |
| --- | --- |
| `AIModelPort` | Common provider contract |
| `OllamaAdapter` | Local model provider |
| `OpenAIAdapter` | Cloud model provider |
| `ModelRegistry` | Capability-to-provider mapping |
| `InferenceRouter` | Primary/fallback execution |
| `CircuitBreaker` | Provider health protection |

## What I Learned

Provider abstraction taught me that AI backend design should not be vendor-first.

It should be capability-first.

The application should say:

```text
I need summarization.
```

The infrastructure should decide:

```text
Use Ollama first, then OpenAI if needed.
```

## Next

Next, we will look at guardrails, Redis caching, response pipelines, and safe error handling.
