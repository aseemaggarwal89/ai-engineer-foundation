# 08 - AI Integration Architecture: From Model Call to Enterprise Pipeline

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)

After learning FastAPI fundamentals, authentication, dependency injection, and routing, I added the part that started the whole project for me:

AI integration.

At first, AI integration looks simple:

```text
receive text
-> call model
-> return response
```

That is enough for a demo.

But backend AI features need more than a model call.

They need request validation, input policy checks, prompt construction, caching, provider routing, fallback, timeout handling, response validation, safe errors, and observability.

This blog explains how the AI summarization flow works in this project.

## The Mental Shift

The biggest shift was this:

> The model is only one step in the AI feature.

The actual backend feature is the pipeline around the model.

In this project, the summarization flow is:

```text
POST /ai/summarize
-> FastAPI request schema
-> route
-> summarize use case
-> input safety and guardrails
-> summary service
-> prompt builder
-> Redis cache lookup
-> inference router
-> model registry
-> provider adapter
-> Ollama or OpenAI
-> response pipeline
-> validated bullets
-> Redis cache write
-> API response
```

That is the difference between "calling an AI model" and building an AI backend feature.

## AI Module Structure

The AI feature is grouped under:

```text
app/application/ai/
```

This folder is not a pure application layer.

It is a feature-oriented AI module that contains multiple internal concerns:

```text
app/application/ai/
├── core/
├── domain/
├── infrastructure/
├── prompts/
├── schemas/
├── services/
├── usecases/
└── validator/
```

The structure is still easy to follow because each folder has a clear responsibility.

## Main Components

Here is the verified responsibility map:

```text
SummaryRequest / SummaryResponse
-> public API request and response contracts

SummarizeTextUseCase
-> application boundary for the summarize operation

SummaryService
-> prompt, cache, inference, pipeline, and cache-write workflow

AIModelPort
-> common provider contract for Ollama and OpenAI

AIInferencePort
-> inference contract used by application services

AIResponseCachePort
-> cache contract used by SummaryService

AIResponsePipeline
-> response processing contract

ModelRegistry
-> maps capabilities to configured provider routes

InferenceRouter
-> selects primary provider and applies fallback

OllamaAdapter / OpenAIAdapter
-> provider-specific HTTP/API calls

RedisAIResponseCache
-> hash-based Redis cache for validated AI outputs

SummarizationPipeline
-> parses, validates, guards, and scores summary bullets

CircuitBreaker
-> provider health gate used by adapters
```

There is also a `ChatPipeline` and chat capability registration, but the active public API in this blog is summarization.

The codebase also contains an `EmbeddingPort` and `OpenAIEmbeddingAdapter` as early building blocks for future RAG work. They are not part of the current `/ai/summarize` request lifecycle.

## API Schema Boundary

The HTTP request schema lives in:

```text
app/application/ai/schemas/ai_summary.py
```

The request body is:

```python
class SummaryRequest(BaseModel):
    text: SummaryText
```

The `text` field is constrained before the use case runs:

```text
strip whitespace
minimum length: 1
maximum length: 20,000 characters
```

The response schema is:

```python
class SummaryResponse(BaseModel):
    bullets: list[str]
```

The API schema does not expose Ollama or OpenAI response formats.

That separation matters.

The route returns application data, not provider data.

## Route Layer

The route lives in:

```text
app/routers/routes/ai.py
```

The route is intentionally thin:

```python
@public_router.post("/summarize", response_model=SummaryResponse)
async def summarize(
    request: SummaryRequest,
    use_case: SummarizeTextUseCase = Depends(get_summarize_use_case),
):
    bullets = await use_case.execute(request.text)
    return SummaryResponse(bullets=bullets)
```

The route does not know:

- which model is used
- whether the provider is local or cloud
- whether Redis has a cached response
- how model output is parsed
- how fallback works

That logic belongs deeper in the AI module.

## Use Case Boundary

The use case lives in:

```text
app/application/ai/usecases/summarize_text.py
```

Its job is to protect the application operation before the model workflow starts.

It does:

```text
request-side safety checks
-> input validation and normalization
-> timeout boundary
-> delegate to SummaryService
```

The use case checks for simple sensitive terms such as:

```text
credit card
cvv
password
ssn
```

Then guardrails validate and normalize the text:

```text
reject empty input
reject oversized input
detect binary-like input
remove control characters
normalize whitespace
truncate to configured soft prompt limit
```

This is not a complete prompt-injection defense.

It is request-side input hygiene and policy enforcement.

That distinction is important.

## Prompt Construction

The prompt builder lives in:

```text
app/application/ai/prompts/summary_prompt.py
```

It creates a controlled instruction template:

```python
class SummaryPrompt:
    VERSION = "v1"

    def build(self, text: str) -> str:
        return (
            "Summarize the following text into EXACTLY 5 short bullet points.\n"
            "Do not explain. Do not add extra text.\n\n"
            f"Text:\n{text}"
        )
```

The prompt has a version.

That version is included in the cache fingerprint so changing the prompt contract can invalidate old cached results.

## Summary Service

The service lives in:

```text
app/application/ai/services/summary_service.py
```

This is the main summarization workflow.

It does:

```text
build prompt
-> build cache key
-> check Redis
-> call inference router on cache miss
-> run response pipeline
-> reject low-quality output
-> cache validated bullets
-> return bullets
```

This keeps the AI workflow in one readable place.

The route stays HTTP-focused.

The use case stays application-boundary focused.

The service owns the summarization-specific AI workflow.

## Cache Design

The cache implementation lives in:

```text
app/application/ai/infrastructure/redis_ai_cache.py
```

The cache key includes:

```text
capability
prompt version and prompt text
model
temperature
max tokens
```

Then the full key input is hashed with SHA-256:

```text
ai_cache:<sha256>
```

This means raw user text is not visible in the Redis key.

The service caches only validated structured bullets, not raw provider output.

Current limitation:

```text
The cache is global. It is not tenant-aware or user-aware yet.
```

For a multi-tenant production system, the cache key should include tenant or user isolation where required.

## Model Registry

The model registry lives in:

```text
app/core/model_registry.py
```

Its responsibility is not to call the model.

Its responsibility is to map capabilities to configured provider adapters.

Conceptually:

```text
summarization
-> primary provider
-> optional fallback provider
```

The actual capability enum lives in:

```text
app/application/ai/domain/ai_capability.py
```

Current capabilities include:

```text
SUMMARIZATION
CHAT
EMBEDDING
```

In the current implementation, the registry stores provider routes from settings and concrete adapters registered by the service container.

It does not currently store cost metadata, health state, context-window size, or dynamic priority scoring.

Those would be useful future improvements.

## Inference Router

The inference router lives in:

```text
app/application/ai/infrastructure/inference_router.py
```

Its job is to:

```text
receive capability
-> ask registry for primary adapter
-> call primary provider
-> use fallback adapter if the primary provider fails
```

Fallback happens only for normalized provider failures:

```python
except AIProviderError:
    fallback = self.registry.get_fallback(capability)
```

That is a good boundary.

The router does not retry validation errors or application errors.

It only handles provider failure.

## Provider Adapters

Provider adapters live in:

```text
app/application/ai/infrastructure/ollama_adapter.py
app/application/ai/infrastructure/openai_adapter.py
```

Both adapters implement the same model port:

```text
AIModelPort.generate(...)
```

The rest of the application calls the same interface whether the provider is:

```text
local Ollama
cloud OpenAI
```

Each adapter translates the common application request into provider-specific API calls.

The Ollama adapter calls:

```text
POST /api/generate
```

The OpenAI adapter calls the OpenAI Responses API through `AsyncOpenAI`.

Both adapters normalize provider failures into:

```text
AIProviderError
```

That allows the inference router to handle fallback without knowing provider-specific exception classes.

## Circuit Breaker Boundary

Circuit breakers live in:

```text
app/application/ai/core/circuit_breakers.py
```

They are used inside provider adapters.

That is the right boundary because the circuit breaker protects provider calls.

The current circuit breaker supports:

```text
CLOSED
OPEN
HALF_OPEN
```

When too many provider failures happen, the circuit opens and blocks new calls for a recovery window.

After the recovery window, one half-open probe is allowed.

## Retry and Timeout

The AI implementation uses multiple resilience controls.

The use case has an async timeout boundary:

```text
app/core/timeout.py
```

Provider adapters use infrastructure retry:

```text
app/core/retry.py
```

The retry policy currently makes two attempts for infrastructure calls.

HTTP clients also have provider timeouts configured from AI settings.

Current limitation:

```text
There is no explicit inference concurrency limiter or queue backpressure yet.
```

That would be important before exposing expensive model calls to heavy traffic.

## Response Pipeline

The summarization response pipeline lives in:

```text
app/application/ai/core/summarization_pipeline.py
```

It performs deterministic response processing:

```text
raw model text
-> raw response validation
-> bullet parsing
-> bullet validation
-> length guard
-> quality scoring
```

The parser lives in:

```text
app/application/ai/core/bullet_parser.py
```

The response validators live in:

```text
app/application/ai/validator/response/
```

The pipeline does not prove that every model statement is factually correct.

It validates structure, rejects obviously broken output, limits bullet length, and applies a quality score.

For factual validation, the future RAG implementation should ground responses in retrieved source documents.

## Observability

The AI flow logs useful metadata such as:

```text
ai_cache_hit
ai_cache_miss
ai_inference_started
ai_inference_completed
ai_inference_response_received
ai_router_primary_attempt
ai_router_primary_provider_failed
ai_router_fallback_attempt
```

The logs include operational fields such as:

```text
provider
model
latency_seconds
prompt_chars
raw_output_chars
capability
```

They do not log the full prompt or full model response in the normal success path.

That is important because prompts may contain user data.

## Production-Oriented Design

I would describe this as a production-oriented learning implementation.

It includes many patterns used in real AI backends:

- thin HTTP routes
- dependency injection
- provider abstraction
- capability-based routing
- local and cloud model support
- provider fallback
- Redis caching
- request guardrails
- response validation
- circuit breakers
- retries and timeouts
- structured logging
- safe exception mapping

It is not the final form of a production AI platform.

The current gaps are also important to understand:

- no tenant-aware cache isolation yet
- no inference queue or concurrency limiter yet
- no token/cost budget tracking yet
- no semantic prompt-injection defense yet
- no factual grounding yet
- no RAG pipeline yet
- no model evaluation dataset yet

Those gaps are not failures.

They are the roadmap.

## Why This Design Helps

The design makes the provider replaceable.

The route does not care if summarization uses Ollama or OpenAI.

The use case does not care how Redis stores cached output.

The summary service does not care about OpenAI exception classes.

The response pipeline does not care which provider produced the raw text.

That is the main benefit of ports and adapters.

Each part has one reason to change.

## What I Learned

My memory hook for this implementation is:

```text
Route receives
Use case protects
Service orchestrates
Cache avoids repeats
Router selects
Adapter calls
Pipeline validates
Response returns
```

The model call is only one box in the workflow.

The real learning is how to design the boxes around it.

## Next

Next, I will go deeper into provider abstraction: Ollama, OpenAI, model registry, inference router, and fallback.
