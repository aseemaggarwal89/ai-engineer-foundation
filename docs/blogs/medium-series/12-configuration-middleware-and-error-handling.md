# 12 - Configuration, Middleware, and Error Handling in a Production-Style FastAPI AI Backend

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


After building routes, authentication, database migrations, and the AI pipeline, I realized there is another layer that is easy to ignore:

```text
How does the application protect itself before business logic runs?
```

This is where configuration, middleware, and exception handling become important.

In a small demo, the endpoint usually calls the model directly.

In a production-style backend, the request passes through several safety and operational layers before it reaches the AI workflow.

## Why This Topic Matters

AI APIs are different from normal CRUD APIs.

They can receive:

- very large prompts
- expensive requests
- unsafe inputs
- repeated duplicate calls
- slow provider responses
- unpredictable model output

So the backend must control the request before and after the model call.

In this project, those controls are not placed randomly inside route handlers.

They are configured at the application level.

## Application Startup Flow

The application starts from:

```text
app/main.py
```

The `create_app()` function is responsible for assembling the FastAPI application.

Its responsibilities include:

- loading settings
- configuring logging
- configuring tracing
- registering middleware
- registering routers
- registering exception handlers
- connecting the AI service container during lifespan startup

This keeps application setup separate from business logic.

## FastAPI Lifespan

The project uses FastAPI lifespan to create long-lived resources once per process.

During startup:

```python
container = ServiceContainer(settings)
await container.startup()
app.state.container = container
```

This container owns reusable AI infrastructure such as:

- Ollama HTTP client
- OpenAI client
- Redis client
- model registry
- inference router
- pipelines
- guardrails

This matters because provider clients and Redis connections should not be recreated for every request.

## Configuration With Pydantic Settings

Configuration lives in:

```text
app/core/config.py
```

The project uses Pydantic settings to load environment values into typed configuration objects.

Example:

```python
class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    ai: AISettings
```

AI settings are nested:

```python
class AISettings(BaseModel):
    provider: AIProvider = AIProvider.OLLAMA
    openai_api_key: str | None = None
    ollama_base_url: str = "http://ollama:11434"
    redis_host: str = "redis"
    redis_port: int = 6379
    timeout_seconds: int = 40
    max_request_bytes: int = 262_144
```

The setting:

```python
env_nested_delimiter = "__"
```

allows environment variables like:

```text
AI__PROVIDER=ollama
AI__OLLAMA_BASE_URL=http://ollama:11434
AI__REDIS_HOST=redis
AI__MODEL_REGISTRY__SUMMARIZATION__PRIMARY=ollama
AI__MODEL_REGISTRY__SUMMARIZATION__FALLBACK=openai
```

This is useful because model routes can be changed without changing application code.

## Fail Fast Configuration

The AI settings validate provider configuration.

For example, if OpenAI is selected or configured as fallback, the application expects a valid OpenAI API key.

This is important because a bad configuration should fail during startup, not after a user sends a request.

Fail fast behavior makes production systems easier to operate.

## Middleware Layer

Middleware runs before and after route handlers.

In this project, middleware handles:

- rate limiting
- metrics
- request IDs
- request body size limits

The request lifecycle looks like this:

```text
HTTP request
-> rate limit middleware
-> metrics middleware
-> request ID middleware
-> body size middleware
-> router
-> use case
-> service
-> AI pipeline
-> response
```

## Request ID Middleware

Request ID middleware gives every request a traceable identity.

It can:

- accept an incoming `X-Request-ID`
- generate one if missing
- attach it to logs
- return it in response headers

This helps connect logs across:

- FastAPI route
- service layer
- Redis cache
- model provider
- response pipeline

For AI backends, this is very useful because model calls can be slow and logs may be spread across multiple services.

## Metrics Middleware

Metrics middleware records HTTP-level behavior.

The app exposes:

```http
GET /metrics
```

This allows Prometheus-style monitoring.

Metrics help answer:

```text
How many requests are coming in?
How slow are endpoints?
Which endpoints are failing?
```

For an AI backend, this can later be extended to track:

- provider latency
- fallback count
- cache hit rate
- token usage
- validation failures
- estimated cost

## Body Size Limit Middleware

AI endpoints need request-size protection.

Without this, a client could send a very large prompt and cause:

- memory pressure
- slow validation
- expensive model calls
- poor user experience

The project uses:

```text
app/core/middleware/body_size.py
```

and configures the maximum request size from:

```text
settings.ai.max_request_bytes
```

This is a transport-level guardrail.

It protects the application before prompt-level guardrails run.

## Rate Limiting

The project uses SlowAPI for rate limiting.

Authentication endpoints use rate limits because login and registration are sensitive operations.

For AI endpoints, rate limiting is also important because each request may call a model provider.

In an enterprise AI API, rate limits can be applied by:

- IP address
- user ID
- tenant ID
- API key
- route
- capability

This prevents accidental overload and helps control cost.

## Exception Handling

Exception handlers live in:

```text
app/core/exception_handlers.py
app/core/exception_registry.py
```

The goal is to convert domain exceptions into consistent HTTP responses.

Instead of returning different error formats from different routes, the app returns a predictable shape:

```json
{
  "error_code": "SERVICE_ERROR",
  "message": "Something went wrong"
}
```

This makes the API easier to consume and debug.

## Why Safe Error Mapping Matters For AI

AI systems can fail in many ways:

- provider timeout
- provider rate limit
- model refusal
- invalid response format
- unsafe prompt
- Redis unavailable
- missing configuration

The API should not expose internal stack traces or provider secrets.

It should return a controlled error message and log the internal details for operators.

## How This Connects To SOLID Principles

This design supports SOLID principles:

| Principle | How it appears in the project |
| --- | --- |
| Single Responsibility | Middleware handles cross-cutting behavior, routes handle HTTP, services handle workflows |
| Open/Closed | New middleware or exception types can be added without rewriting routes |
| Dependency Inversion | Use cases and services depend on ports and settings, not concrete provider APIs |
| Interface Segregation | AI providers, cache, and pipelines have focused contracts |

## Common Debugging Scenario

Suppose the API returns a request-size error.

The model provider was never called.

The failure happened before the route reached the AI pipeline.

That tells me:

```text
Problem area: middleware or input size
Not problem area: Ollama, OpenAI, Redis, model registry, response pipeline
```

This is why understanding the request path matters.

## What I Learned

Configuration, middleware, and exception handling are not secondary topics.

They are part of the AI backend design.

The model call is only one step.

The backend must also control:

- startup behavior
- environment-specific configuration
- request identity
- request size
- rate limits
- error responses
- operational visibility

## Next

After understanding how the application protects and configures itself, the next useful topic is testing, debugging, and preparing the public repository.
