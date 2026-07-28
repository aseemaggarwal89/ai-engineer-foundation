# 04 - Understanding Async Programming in FastAPI

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


After learning project structure and database migrations, the next concept I needed to understand was async programming.

FastAPI supports both normal functions and async functions.

At first, async can feel confusing because it introduces two keywords:

```python
async
await
```

But the basic idea is simple:

> Async lets the application wait for slow I/O without blocking the whole server.

That matters a lot in AI backends.

AI backends do not only run Python code.

They wait for many external systems:

- database queries
- Redis calls
- Ollama HTTP requests
- OpenAI API calls
- tracing exporters
- network services

While one request is waiting for a model provider, the server should still be able to work on other requests.

That is where async helps.


## What Is I/O?

I/O means input/output.

In backend applications, common I/O operations include:

- calling another API
- querying a database
- reading from Redis
- writing to Redis
- waiting for a model provider
- sending traces to an observability system

These operations are slow compared to in-memory Python operations.

For example, building a prompt string is fast.

Calling Ollama or OpenAI can take seconds.

Async allows Python to pause the current request while it waits and let the event loop continue handling other work.

## A Simple Mental Model

Think of async like this:

```text
Request A starts
Request A waits for Ollama
Server works on Request B
Request A receives Ollama response
Request A continues
```

Without async-friendly I/O, one slow operation can hold up worker capacity.

With async, waiting becomes more efficient.

Async does not make the model faster.

It makes the server better at handling waiting.

## Async Route Example

The AI route is async:

```python
async def summarize(...):
    bullets = await use_case.execute(request.text)
    return SummaryResponse(bullets=bullets)
```

The route uses `await` because summarization eventually calls async operations:

- Redis cache lookup
- model provider HTTP request
- Redis cache write
- async service methods

The route itself stays small.

It does not know the full AI workflow.

It simply awaits the use case and returns a response.

## Async Use Case

The summarization use case is also async:

```python
async def execute(self, text: str) -> list[str]:
    self.safety.check(text)
    text = self.guardrails.validate_prompt(text)
    return await self.summary_service.summarize(text)
```

Notice something important:

```python
self.safety.check(text)
self.guardrails.validate_prompt(text)
```

These calls are synchronous.

That is fine because they run in memory.

They validate strings and do not wait for external systems.

But this call is awaited:

```python
return await self.summary_service.summarize(text)
```

The service may call Redis and model providers, so it is async.

## Async Service

The summary service orchestrates the AI workflow.

It performs async cache and inference calls:

```python
cached = await self.cache.get(cache_key)

raw_output = await self.inference.generate(
    capability=AICapability.SUMMARIZATION,
    prompt=prompt_text,
    temperature=self.settings.temperature,
    max_tokens=self.settings.max_tokens,
)

await self.cache.set(cache_key, json.dumps(bullets), ttl=3600)
```

Redis and model calls are I/O.

That is why they are awaited.

The response pipeline, however, can stay synchronous because it validates and transforms data in memory:

```python
bullets, score = pipeline.run(raw_output)
```

This is a useful pattern:

```text
I/O work -> async
in-memory transformation -> sync
```

## Async Provider Adapter

The Ollama adapter uses an async HTTP client:

```python
response = await self.client.post(
    "/api/generate",
    json=payload,
)
```

This is important because local model calls can take several seconds.

While Ollama is generating, the FastAPI server should not block every other request.

The adapter awaits the provider response, normalizes the result, and returns generated text to the inference router.

## Async Database Sessions

The database layer uses async SQLAlchemy.

Database sessions are created through a FastAPI dependency:

```python
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

Repository methods can then await database operations:

```python
result = await self._session.execute(...)
await self._session.commit()
```

This fits naturally with FastAPI's async request handling.

When routes, use cases, repositories, Redis clients, and HTTP clients all follow async patterns, the request lifecycle stays consistent.

## Request Timeline For AI Summarization

The async request lifecycle for summarization looks like this:

```text
POST /ai/summarize
-> async route awaits use case
-> use case runs sync safety checks
-> use case awaits summary service
-> service awaits Redis cache lookup
-> if cache miss, service awaits inference router
-> router awaits provider adapter
-> adapter awaits Ollama or OpenAI HTTP response
-> service runs sync response pipeline
-> service awaits Redis cache write
-> route returns response
```

Not every step is async.

Only the waiting steps are async.

That is the key idea.

## When To Use `async def`

Use `async def` when the function:

- calls async database operations
- calls Redis
- calls HTTP APIs
- calls model providers
- awaits another async function
- manages async resources with `async with`

Use normal `def` when the function:

- only transforms data
- validates strings
- builds prompts
- parses model output
- computes scores
- maps domain objects

Example:

```python
def build(self, text: str) -> str:
    return f"Summarize: {text}"
```

Prompt building does not need async.

It does not wait for a database, Redis, or network service.

## Common Mistake: Making Everything Async

A common mistake is making every function async.

That does not automatically improve performance.

Async is useful when the function performs I/O or awaits another async function.

If a function only formats a string, parses a response, or checks a list of rules, normal `def` is simpler and clearer.

Readable code matters.

## Common Mistake: Blocking Inside Async Code

Another common mistake is using blocking calls inside async functions.

Examples:

```python
time.sleep(5)
requests.post(...)
```

inside an async route or async service.

These calls block the event loop.

Better async-friendly alternatives are:

```python
await asyncio.sleep(5)
await httpx.AsyncClient().post(...)
```

In this project, the provider adapters use async HTTP clients, which keeps the model calls async-friendly.

## Timeout Handling

AI systems need timeouts.

Model calls can be slow.

Network calls can hang.

External services can become unavailable.

The project has timeout support in:

```text
app/core/timeout.py
```

The decorator uses:

```python
await asyncio.wait_for(...)
```

If an operation takes too long, it raises a controlled service error.

This is important because an AI backend should not allow one request to wait forever.

## Debugging Async Requests

When async code fails, the problem is often one of these:

- a missing `await`
- a blocking call inside async code
- a timeout from an external service
- an unclosed async client
- a database session lifecycle issue
- an exception swallowed by a background task

For this project, useful logs include:

```text
ai_cache_hit
ai_cache_miss
ai_inference_started
ai_inference_completed
ai_inference_response_received
```

These logs help identify where the request spent time.

For example:

```text
ai_cache_miss
ai_inference_started
12 seconds later
ai_inference_completed
```

This means the request waited on model inference.

That is expected for local model generation.

## Why Async Matters For AI Backends

Async is valuable in this project because the AI workflow waits on multiple systems.

For summarization, the backend may call:

```text
Redis
Ollama or OpenAI
Redis again
```

For future RAG, the backend may call:

```text
database
embedding model
vector search
generation model
cache
observability tools
```

That makes async programming an important foundation for AI backend engineering.

## What I Learned

Async programming is not magic.

It is a way to handle many I/O-heavy requests efficiently.

The biggest lesson for me was:

```text
Use async for waiting.
Keep pure in-memory logic synchronous.
```

That balance keeps the code scalable and readable.

## Next

In the next post, I will explain routing in FastAPI and how APIs are organized in this project.
