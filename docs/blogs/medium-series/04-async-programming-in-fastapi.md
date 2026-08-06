# 04 - Understanding Async Programming in FastAPI

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)

After learning project structure and database migrations, the next concept I wanted to understand was async programming.

FastAPI supports both synchronous and asynchronous code. At first, this can feel confusing because `async` and `await` look like magic keywords.

But the practical idea is simple:

> Async helps the application wait for slow I/O without blocking the event loop.

That matters a lot in AI backends.

An AI backend waits for many external systems:

- PostgreSQL database queries
- Redis cache calls
- Ollama HTTP requests
- OpenAI API calls
- observability and tracing infrastructure
- other network services

If one request is waiting for a model provider, the server should still be able to handle other ready requests.

Async does not make the model faster. It makes the backend better at using time while it is waiting.

## What Async Really Means

An `async def` function creates a coroutine function.

The important scheduling moment happens at `await`.

When a coroutine awaits an incomplete I/O operation, it yields control to the event loop. The event loop can then run another ready task while the first operation is waiting.

A simplified timeline looks like this:

```text
Request A starts
Request A awaits Ollama HTTP response
Event loop runs Request B
Ollama response arrives
Event loop resumes Request A
Request A returns response
```

This is cooperative scheduling.

It does not mean everything runs at the same time.

It also does not mean Python automatically creates parallel execution. The benefit appears when the code uses async-aware clients and actually awaits I/O.

## What Is I/O?

I/O means input/output.

In backend applications, common I/O operations include:

- calling another API
- querying a database
- reading from Redis
- writing to Redis
- waiting for a model provider
- sending traces to an observability system

These operations are slow compared to small in-memory Python work.

For example, building a prompt string is fast.

Calling Ollama or OpenAI can take seconds.

That is why this project uses async for database, cache, and model-provider boundaries.

## FastAPI Sync And Async Routes

FastAPI supports both styles:

```python
def route_handler():
    ...
```

and:

```python
async def route_handler():
    ...
```

Synchronous route handlers and synchronous dependencies are normally run by FastAPI in a thread pool.

Async route handlers execute on the event loop.

That difference matters:

- blocking code inside `async def` can block the event loop
- blocking code inside `def` usually consumes a thread-pool worker
- too much blocking work can exhaust thread-pool capacity
- synchronous routes are not inherently wrong
- async routes are appropriate when the call chain uses async clients

So the rule is not:

```text
Everything must be async.
```

The better rule is:

```text
Use async where the request flow awaits async I/O.
Keep simple synchronous logic synchronous.
```

## Async Route In This Project

The AI summarization endpoint is:

```text
POST /ai/summarize
```

The route lives in:

```text
app/routers/routes/ai.py
```

The route is async because it awaits the summarization use case:

```python
@public_router.post("/summarize", response_model=SummaryResponse)
async def summarize(
    request: SummaryRequest,
    use_case: SummarizeTextUseCase = Depends(get_summarize_use_case),
):
    bullets = await use_case.execute(request.text)
    return SummaryResponse(bullets=bullets)
```

The HTTP layer stays thin.

It validates the request schema, calls the use case, and returns the response schema.

It does not know how Redis, Ollama, OpenAI, fallback, or response validation work.

## Dependency Injection

The route receives its use case through FastAPI dependency injection:

```text
app/dependencies/ai_dependencies.py
```

The dependency chain builds request-level application objects from long-lived infrastructure stored in:

```text
request.app.state.container
```

That container is created during application lifespan startup in:

```text
app/main.py
```

This separation keeps request code readable:

- routes depend on use cases
- use cases depend on services and validators
- services depend on ports and registries
- adapters own provider-specific implementation details

## Async Use Case

The summarization use case lives in:

```text
app/application/ai/usecases/summarize_text.py
```

Its flow is:

```python
@timeout_from_self
async def execute(self, text: str) -> list[str]:
    self.safety.check(text)
    text = self.guardrails.validate_prompt(text)

    return await self.summary_service.summarize(text)
```

Two calls are synchronous:

```python
self.safety.check(text)
self.guardrails.validate_prompt(text)
```

That is intentional.

They run in memory. They validate strings and do not call external systems.

The service call is awaited:

```python
await self.summary_service.summarize(text)
```

That method can call Redis and model providers, so it belongs in the async path.

## Async Summary Service

The summary service lives in:

```text
app/application/ai/services/summary_service.py
```

It owns the main AI application workflow:

```text
prompt build
-> cache key build
-> Redis cache lookup
-> inference call on cache miss
-> response pipeline
-> Redis cache write
```

The cache lookup is async:

```python
cached = await self.cache.get(cache_key)
```

If a cached value exists, the service returns it and does not call the provider.

On a cache miss, inference is async:

```python
raw_output = await self.inference.generate(
    capability=AICapability.SUMMARIZATION,
    prompt=prompt_text,
    temperature=self.settings.temperature,
    max_tokens=self.settings.max_tokens,
)
```

After the model response is validated and parsed, the versioned cache write is async:

```python
await self.cache.set(
    cache_key,
    json.dumps({"schema_version": 1, "bullets": bullets}),
    ttl=self.settings.cache_ttl_seconds,
)
```

The cache TTL is now configured through the AI cache settings.

## Synchronous Work Inside The Async Flow

Not every step should be async.

This project keeps lightweight in-memory logic synchronous:

- input safety checks
- prompt construction
- cache key construction
- response parsing
- response validation
- small scoring rules
- domain mapping

For example, the response pipeline is synchronous:

```python
pipeline = self.pipeline_registry.get(AICapability.SUMMARIZATION)
bullets, score = pipeline.run(raw_output)
```

That pipeline currently performs deterministic, lightweight work:

```text
raw text
-> validate raw response
-> parse bullets
-> validate bullets
-> suspicious-output length guard
-> structural score
```

The service rejects output that does not satisfy the summary response contract:

```python
if score < self.threshold:
    raise ResponseValidationError(
        "AI output did not satisfy the summary response contract"
    )
```

This is a useful design pattern:

```text
Async I/O waiting -> async and await
Small, fast in-memory work -> synchronous
Blocking I/O without an async API -> isolate only when necessary
CPU-intensive work -> process, worker, task queue, or separate service
```

## CPU-Bound Work Is Different

Async is great for waiting.

It is not a solution for heavy CPU work.

Examples of CPU-heavy work include:

- large-document parsing
- image processing
- heavy tokenization
- large response transformations
- local embedding generation
- running ML inference inside the FastAPI process
- expensive quality scoring

CPU-heavy work can block the event loop even when no external network call is happening.

For production systems, this kind of work often belongs in:

- a process pool
- a background worker
- a task queue
- a separate inference service
- a dedicated model server

This is especially important for AI systems.

If inference runs directly inside the FastAPI process, declaring the route async does not prevent CPU- or GPU-bound inference from blocking application execution.

In this project, Ollama runs as an external service. FastAPI waits for it over asynchronous HTTP.

That is why async helps here.

## Async Provider Adapters

The Ollama adapter lives in:

```text
app/application/ai/infrastructure/ollama_adapter.py
```

It uses a reusable `httpx.AsyncClient`:

```python
response = await self.client.post(
    "/api/generate",
    json=payload,
)
```

This is the right shape for async HTTP.

The client is not created inside every provider call.

It is created once in the AI service container:

```text
app/application/ai/core/container.py
```

The OpenAI adapter lives in:

```text
app/application/ai/infrastructure/openai_adapter.py
```

It uses `AsyncOpenAI`:

```python
response = await self.client.responses.create(
    model=model,
    input=prompt,
    temperature=temperature,
    max_output_tokens=max_tokens,
)
```

This distinction matters:

> Calling an external service is asynchronous only when the selected client library exposes an async API and the operation is awaited.

In this project:

- PostgreSQL uses SQLAlchemy `AsyncSession`
- Redis uses `redis.asyncio.Redis`
- Ollama uses `httpx.AsyncClient`
- OpenAI uses `AsyncOpenAI`

That is why those calls fit inside async routes and services.

## Reusable Client Lifecycle

Creating a new HTTP client for every request is inefficient because it creates a new connection pool repeatedly.

This project uses lifespan-managed clients instead.

During FastAPI startup:

```text
app/main.py
-> ServiceContainer(settings)
-> reusable Ollama client
-> optional reusable OpenAI client
-> reusable Redis client
```

During shutdown:

```python
await self.ollama_client.aclose()
if hasattr(self, "openai_client"):
    await self.openai_client.close()
await self.redis.aclose()
```

That gives the application a clean resource lifecycle:

- create clients once
- inject clients into adapters
- reuse connection pools
- close clients during shutdown

## Async Database Sessions

The database setup lives in:

```text
app/db/db.py
```

It creates an async SQLAlchemy engine:

```python
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)
```

It also creates an async session factory:

```python
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
```

The FastAPI database dependency yields one async session for the request:

```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

Repository methods await database operations:

```python
result = await self._session.execute(...)
await self._session.commit()
```

In this project, user repository methods currently own their own commit calls.

Audit logging uses its own session factory and commits inside the audit repository because audit events may run outside the main request transaction.

In larger systems, the transaction boundary may live in a repository, service, use case, or unit-of-work layer. The important point is that ownership should be intentional.

One warning I learned:

> A request-scoped `AsyncSession` should not be shared across multiple concurrently executing tasks.

An `AsyncSession` represents mutable transactional state. Each request or unit of work should receive its own database session.

## Timeout Handling

The timeout utility lives in:

```text
app/core/timeout.py
```

It uses `asyncio.wait_for`:

```python
return await asyncio.wait_for(
    func(self, *args, **kwargs),
    timeout=self.timeout_seconds,
)
```

If the operation exceeds the configured timeout, it raises a controlled `ServiceError`.

This decorator is used on the summarization use case and async repository methods.

Provider calls also have client-level timeout configuration through the shared Ollama and OpenAI clients.

Timeouts are important in AI systems because model providers can become slow or unavailable. A backend should fail safely instead of waiting forever.

## Handling Unavoidable Blocking I/O

Sometimes a library does not provide an async API.

If that blocking I/O must be used inside an async request path, isolate it carefully:

```python
result = await asyncio.to_thread(
    blocking_io_function,
    argument,
)
```

This is for unavoidable blocking I/O.

It is not a generic fix for heavy CPU processing, long-running model inference, unsafe shared state, or unlimited background work.

In this project’s verified async AI path, I did not find direct `requests`, `urllib`, `time.sleep`, synchronous Redis calls, or synchronous SQLAlchemy calls inside async execution.

## Summarization Request Lifecycle

The verified request lifecycle is:

```text
POST /ai/summarize
-> SummaryRequest schema validation
-> async route handler
-> FastAPI dependency builds SummarizeTextUseCase
-> use case runs sync safety checks
-> use case runs sync prompt guardrails
-> use case awaits SummaryService
-> service builds prompt synchronously
-> service builds cache key synchronously
-> service awaits Redis cache lookup
-> cache hit returns validated cached bullets
-> cache miss awaits InferenceRouter
-> router awaits primary provider adapter
-> adapter awaits Ollama or OpenAI
-> router may await fallback provider if primary fails
-> service runs sync response pipeline
-> service awaits Redis cache write
-> SummaryResponse schema is returned
```

The core idea is:

```text
Only the waiting steps are async.
The deterministic in-memory steps stay synchronous.
```

## Logging And Tracing

The AI flow emits structured log events such as:

```text
ai_cache_hit
ai_cache_miss
ai_inference_started
ai_inference_completed
ai_inference_response_received
```

The provider adapters log provider name, model name, prompt length, and latency.

The summary service logs cache behavior and raw output length.

It does not log full prompts or raw model responses in the normal success path.

Request IDs are attached through request context middleware and structured logging.

OpenTelemetry tracing is optional and configured when an OTLP endpoint is present. Observability libraries may record spans during request processing and export them asynchronously or in batches depending on configuration.

## Async Concurrency Is Not Unlimited Concurrency

Async makes waiting more efficient, but downstream systems still have limits.

The backend still has to respect:

- database connection pools
- Redis capacity
- HTTP client connection pools
- Ollama runtime capacity
- OpenAI provider quotas
- worker-process limits
- timeout budgets
- retry behavior

This project already includes:

- provider timeouts
- retry wrappers for infrastructure calls
- provider circuit breakers
- request body size limits
- route rate limiting infrastructure
- structured logs for latency and failures

The project does not yet implement an explicit model-provider concurrency limiter such as an `asyncio.Semaphore` or bounded queue.

That is a future production improvement, especially if traffic grows or model providers need strict backpressure.

## What I Learned

Async programming is not magic.

It is a disciplined way to handle I/O-heavy request flows.

For this project, the most important learning was:

```text
Use async when the code awaits async I/O.
Keep simple in-memory workflow steps synchronous.
Move heavy CPU or model execution away from the event loop.
Close reusable clients during application shutdown.
Do not treat async as unlimited concurrency.
```

This gives the backend a clean foundation for AI features today and future RAG integration later.

## Next

In the next post, I will explain routing in FastAPI and how APIs are organized in this project.
