# Understanding Async Programming in FastAPI

FastAPI supports async programming, and this project uses async heavily.

At first, async can feel confusing.

But the basic idea is simple:

> Async lets the application wait for slow I/O without blocking the whole server.

AI backends do a lot of I/O.

They wait for:

- database queries
- Redis calls
- Ollama HTTP requests
- OpenAI API calls
- tracing exporters
- network services

That makes async important.

## What Is I/O?

I/O means input/output.

In backend applications, common I/O operations include:

- calling another API
- querying a database
- reading from Redis
- waiting for a model provider

These operations are slow compared to CPU instructions.

Async allows Python to work on other requests while waiting.

## Async Route Example

The AI route is async:

```python
async def summarize(...):
    bullets = await use_case.execute(request.text)
    return SummaryResponse(bullets=bullets)
```

The route uses `await` because summarization eventually calls:

- Redis
- model provider HTTP endpoint
- async service methods

## Async Use Case

The summarization use case is also async:

```python
async def execute(self, text: str) -> list[str]:
    self.safety.check(text)
    text = self.guardrails.validate_prompt(text)
    return await self.summary_service.summarize(text)
```

The safety and guardrail checks are synchronous because they run in memory.

The service call is awaited because it can perform I/O.

## Async Service

The summary service does async cache and inference calls:

```python
cached = await self.cache.get(cache_key)
raw_output = await self.inference.generate(...)
await self.cache.set(cache_key, json.dumps(bullets), ttl=3600)
```

Redis and model calls are I/O, so they are awaited.

## Async Provider Adapter

The Ollama adapter uses an async HTTP client:

```python
response = await self.client.post("/api/generate", json=payload)
```

This is important because model calls can take seconds.

While Ollama is generating, the server should not block every other request.

## Async Database Sessions

The database layer uses async SQLAlchemy.

That allows database queries to be awaited:

```python
result = await self._session.execute(...)
await self._session.commit()
```

This fits naturally with FastAPI's async request handling.

## When To Use async def

Use `async def` when the function:

- calls async database operations
- calls Redis
- calls HTTP APIs
- calls model providers
- awaits another async function

Use normal `def` when the function:

- only transforms data
- validates strings
- builds prompts
- parses model output
- computes scores

Example:

```python
def build(self, text: str) -> str:
    return f"Summarize: {text}"
```

Prompt building does not need async.

## Common Mistake

A common mistake is making everything async.

That does not help.

Async is useful when the function performs I/O or awaits another async function.

Keep simple CPU-only functions synchronous.

## Timeout Handling

The project uses a timeout decorator:

```text
app/core/timeout.py
```

This prevents operations from running forever.

For AI systems, this is important because model calls can be slow.

## What I Learned

Async programming is not magic.

It is a way to handle many I/O-heavy requests efficiently.

For AI backends, async is especially useful because model providers and databases can be slow.

## Next

After async programming, the next topic is routing and how APIs are organized in FastAPI.

