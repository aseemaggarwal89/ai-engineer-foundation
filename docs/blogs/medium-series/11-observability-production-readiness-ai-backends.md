# 11 - Observability and Production Readiness for AI Backends

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)

In the previous blog, I explained the reliability layer around the AI request:

```text
request checks
-> prompt boundaries
-> Redis cache
-> response pipeline
-> safe errors
```

Once that workflow exists, the next question becomes:

```text
How do I debug and operate this backend when something goes wrong?
```

This is where observability matters.

For an AI backend, a slow or failed request can come from many places:

- request validation
- authentication
- body-size middleware
- Redis cache
- provider routing
- Ollama
- OpenAI
- circuit breaker state
- response validation
- database checks
- tracing infrastructure

Without observability, all of these failures feel the same.

With observability, I can ask better questions:

```text
Did the request reach FastAPI?
Was it rejected before the route?
Was this a cache hit or miss?
Which provider was selected?
Did fallback happen?
How long did inference take?
Did the provider fail or did response validation fail?
Did tracing export fail even though the AI request worked?
```

That distinction is the heart of this post.

## Verified Implementation Files

The observability implementation is spread across these files:

```text
app/core/logging.py
app/core/request_context.py
app/core/middleware/request_id.py
app/core/metrics.py
app/core/middleware/metrics_middleware.py
app/routers/routes/metrics.py
app/core/tracing.py
app/core/tracer.py
app/core/middleware/body_size.py
app/main.py
app/application/ai/services/summary_service.py
app/application/ai/infrastructure/inference_router.py
app/application/ai/infrastructure/ollama_adapter.py
app/application/ai/infrastructure/openai_adapter.py
docker-compose.yml
otel-config.yaml
```

The implementation currently has:

- structured JSON logs
- bounded request ID correlation
- HTTP request metrics with route-template path labels
- `/metrics` endpoint
- optional OpenTelemetry tracing
- FastAPI instrumentation
- SQLAlchemy instrumentation
- provider inference logs
- cache hit, miss, and invalid-cache logs
- local Jaeger and OpenTelemetry Collector in Docker Compose

It does not yet have full AI-specific Prometheus metrics for provider latency, fallback count, token usage, or cost.

Those are production roadmap items.

## Structured JSON Logging

Logging is configured in:

```text
app/core/logging.py
```

The app writes JSON logs to stdout using a custom formatter.

Each log includes:

```text
timestamp
level
logger
message
request_id, when available
extra metadata
```

The formatter also captures `extra={...}` fields from log calls.

It also converts common non-JSON values such as `UUID`, `date`, and `datetime` into strings. If a custom `extra` value is not JSON serializable, the formatter falls back to `repr(value)` so logging does not break the request path.

When `exc_info` is present, the formatter adds an `exception` field with the formatted server-side traceback.

That means code like this:

```python
logger.info(
    "ai_inference_completed",
    extra={
        "provider": "ollama",
        "model": "tinyllama",
        "latency_seconds": latency,
    },
)
```

becomes a structured log record.

Conceptually, the output looks like:

```json
{
  "timestamp": "2026-07-18T11:59:07.547982+00:00",
  "level": "INFO",
  "logger": "app.application.ai.infrastructure.ollama_adapter",
  "message": "ai_inference_completed",
  "request_id": "98754ae8-41d0-4a4f-aaae-b194fd28831c",
  "provider": "ollama",
  "model": "tinyllama",
  "latency_seconds": 12.39
}
```

This is better than plain text logs because the logs become searchable by fields:

```text
request_id
provider
model
latency_seconds
capability
category
fallback_eligible
```

## Why JSON Logs Matter

In a small project, logs are often read directly in the terminal.

In a backend service, logs usually go to a platform such as:

```text
CloudWatch
Datadog
Grafana Loki
ELK
OpenSearch
```

Structured logs are easier to search and aggregate.

For example, I can search:

```text
message = ai_inference_completed
provider = ollama
latency_seconds > 10
```

That is much easier than scanning plain strings manually.

## Request ID Correlation

Request ID support lives in:

```text
app/core/request_context.py
app/core/middleware/request_id.py
```

The middleware does four things:

```text
read X-Request-ID if the client or gateway sent a safe bounded value
-> create a UUID if missing or invalid
-> store it in a ContextVar
-> return X-Request-ID in the response headers
```

The project does not blindly trust arbitrary client-provided request IDs.

Client request IDs are reused only when they match a bounded safe format:

```text
letters, numbers, dot, underscore, colon, hyphen
1 to 128 characters
```

Values with spaces, newlines, control characters, or excessive length are replaced with a generated UUID.

The context variable is:

```python
request_id_ctx: ContextVar[Optional[str]]
```

The logging formatter reads from that context variable and automatically adds `request_id` to logs.

The middleware resets the context variable in a `finally` block, which prevents request IDs from leaking across async requests.

That means one request can be followed across:

```text
route
use case
service
cache
inference router
provider adapter
exception handler
```

This is especially useful for AI calls because provider latency can be several seconds.

Without a request ID, it is hard to know which model log belongs to which HTTP request.

## HTTP Metrics

Metrics are defined in:

```text
app/core/metrics.py
```

The middleware lives in:

```text
app/core/middleware/metrics_middleware.py
```

The current metrics are:

```text
http_requests_total
http_request_duration_seconds
http_request_errors_total
```

They are labeled by:

```text
method
path
status, for request count
```

The `path` label uses the matched route template when available.

For example:

```text
/users/{user_id}
```

is preferred over:

```text
/users/1001
/users/1002
```

This avoids unbounded Prometheus label cardinality from dynamic URL values.

The metrics endpoint is:

```http
GET /metrics
```

The route lives in:

```text
app/routers/routes/metrics.py
```

In the current project, `/metrics` is public.

For production deployment, I would normally expose it only through an internal network path, monitoring ingress, service mesh policy, or infrastructure-level access control.

This is enough to answer HTTP-level questions:

```text
How many requests are coming in?
Which routes are slow?
Which routes are returning errors?
```

It does not yet answer all AI-level questions.

For example, the project does not currently expose Prometheus counters for:

- AI cache hits and misses
- fallback attempts
- provider failures by category
- response-validation failures
- token usage
- estimated cost

Those are useful future metrics.

## OpenTelemetry Tracing

Tracing is configured in:

```text
app/core/tracing.py
```

Tracing is optional.

In `app/main.py`, tracing is enabled only when this setting exists:

```text
AI__OTLP_ENDPOINT
```

The Docker Compose file sets:

```text
AI__OTLP_ENDPOINT=http://otel-collector:4317
```

The tracing setup wires:

```text
FastAPI instrumentation
SQLAlchemy instrumentation
OTLP trace exporter
BatchSpanProcessor
service.name metadata
```

FastAPI instrumentation captures request spans.

SQLAlchemy instrumentation captures database spans.

The app sends spans to the OpenTelemetry Collector.

The collector then forwards traces to Jaeger.

Trace export happens through the OpenTelemetry SDK and `BatchSpanProcessor`.

That means trace export is not designed to be the synchronous source of truth for whether the API request itself succeeds. If the collector is unavailable, the exporter can emit diagnostics while the product request can still complete.

## Local Tracing Stack

The local Docker stack includes:

```text
python_ai
postgres
ollama
redis
jaeger
otel-collector
```

The Jaeger UI is exposed at:

```text
http://127.0.0.1:16686
```

The OpenTelemetry Collector configuration lives in:

```text
otel-config.yaml
```

The collector receives OTLP traffic on:

```text
4317 for gRPC
4318 for HTTP
```

and exports traces to Jaeger.

This local setup is useful because it makes the project feel closer to a real backend environment.

I am not just running FastAPI alone.

I am running the app with supporting infrastructure.

## Custom Tracing Decorator

There is also a small tracing helper:

```text
app/core/tracer.py
```

It provides:

```python
@traced("span.name")
```

Some use cases and the OpenAI adapter use this helper.

For example, the OpenAI adapter uses:

```python
@tracer.traced("ai.generate")
```

This creates a custom span around that async function.

The Ollama adapter currently has a commented tracing decorator.

That means OpenAI has a custom provider span, while Ollama mainly relies on logs and surrounding request tracing.

That is a useful implementation detail to remember.

## AI Provider Logs

The provider adapters log key AI inference events.

The common success events include:

```text
ai_inference_started
ai_inference_completed
```

The start event includes:

```text
provider
model
prompt_chars
```

The completion event includes:

```text
provider
model
latency_seconds
```

This answers:

```text
Which provider ran?
Which model ran?
How large was the prompt?
How long did inference take?
```

The logs use prompt length, not raw prompt text.

That is important because prompts can contain user content.

Latency is measured with monotonic timing using `time.perf_counter()`, which is the right tool for elapsed-time measurement.

## Provider Failure Logs

The provider adapters normalize vendor or transport failures into `AIProviderError`.

They also log events such as:

```text
ai_timeout
ai_rate_limited
ai_transport_error
ai_authentication_error
ai_invalid_request
ai_provider_error
ai_empty_response
ai_unknown_failure
ai_circuit_prevented_request
```

These logs include metadata such as:

```text
provider
model
status_code
category
```

Some provider exception logs include server-side exception information through `logger.exception(...)`. That is useful for debugging, but in production I would review vendor exception payloads carefully and avoid logging raw provider response bodies, prompts, authorization headers, or API keys.

The router then decides whether fallback is allowed based on the normalized category and fallback eligibility.

This makes debugging easier because I do not have to inspect OpenAI SDK exceptions or raw `httpx` exceptions in the application service.

The adapter converts them into application-level provider failure categories.

## Inference Router Logs

The inference router lives in:

```text
app/application/ai/infrastructure/inference_router.py
```

It logs:

```text
ai_router_primary_attempt
ai_router_primary_provider_failed
ai_router_fallback_attempt
ai_router_no_fallback_configured
ai_router_total_provider_failure
```

The primary failure log includes:

```text
provider
model
category
fallback_eligible
```

This is useful because provider fallback can hide the original failure from the user.

The API client may only see a successful response.

The logs still show that fallback happened.

## Cache Logs

The summary service logs cache behavior:

```text
ai_cache_hit
ai_cache_miss
ai_cache_invalid
```

These logs come from:

```text
app/application/ai/services/summary_service.py
```

Cache logs are useful because two requests with the same input may behave differently:

```text
first request
-> cache miss
-> provider call
-> response validation
-> cache write

second request
-> valid cache hit
-> no provider call
```

If I am testing provider latency, I need to know whether the provider was actually called.

A fast response may mean the model is fast.

Or it may mean Redis returned a cached result.

## Body Size Middleware

Request-size protection lives in:

```text
app/core/middleware/body_size.py
```

This middleware checks the `Content-Length` header before FastAPI reads the body.

The limit comes from:

```text
AI__MAX_REQUEST_BYTES
```

The default is:

```python
max_request_bytes: int = 262_144
```

That is 256 KB.

If the request is too large, the middleware returns:

```json
{
  "error_code": "REQUEST_TOO_LARGE",
  "message": "Request body exceeds the allowed size."
}
```

with:

```text
HTTP 413
```

If `Content-Length` is malformed or negative, it returns a structured `HTTP 400` response with:

```text
INVALID_CONTENT_LENGTH
```

This middleware currently enforces the declared `Content-Length` header.

It does not count streamed request-body bytes when `Content-Length` is missing. That means it is an early header-based protection, not complete streaming body-size enforcement.

This is separate from the AI prompt character limit.

The body-size middleware protects transport and application memory.

The prompt limit protects the AI workflow.

## Middleware Order

The application wires middleware in:

```text
app/main.py
```

The configured middleware includes:

```text
SlowAPI middleware
MetricsMiddleware
RequestIDMiddleware
BodySizeLimitMiddleware
```

Starlette executes middleware in last-added-first order for inbound requests.

Since `app/main.py` adds them in that order, the effective inbound order is:

```text
BodySizeLimitMiddleware
-> RequestIDMiddleware
-> MetricsMiddleware
-> SlowAPI middleware
-> route handler
```

The outbound response flows back in reverse:

```text
route handler
-> SlowAPI middleware
-> MetricsMiddleware
-> RequestIDMiddleware
-> BodySizeLimitMiddleware
```

This matters because an oversized request can be rejected before request ID and metrics middleware run.

This gives the application:

- rate-limit handling
- HTTP metrics
- request ID correlation
- body-size rejection

Middleware ordering matters in production systems because it affects which components see a request before rejection.

For this project, the important learning is that cross-cutting concerns belong around the route handlers, not inside every route.

## Debugging Scenario 1: AI Works, Tracing Fails

Example logs:

```text
ai_inference_completed
ai_inference_response_received
Failed to export traces to otel-collector:4317
```

This means the model call worked.

The response came back.

The tracing exporter failed.

In this project, that trace-export failure is an observability-path problem, not proof that the summarization request failed.

So the bug is probably not in:

```text
Ollama
OpenAI
summary pipeline
response validation
```

The issue is likely in:

```text
OpenTelemetry Collector
Jaeger
networking
AI__OTLP_ENDPOINT
Docker Compose service readiness
```

This is a small example of why observability matters.

It helps separate product-path failures from observability-path failures.

## Debugging Scenario 2: Slow Summarization

If summarization is slow, I would check logs in this order:

```text
request_id
-> ai_cache_hit or ai_cache_miss
-> ai_router_primary_attempt
-> ai_inference_started
-> ai_inference_completed latency_seconds
-> ai_inference_response_received raw_output_chars
```

If there is a cache miss and inference latency is high, the provider call is likely the slow part.

If there is a cache hit and the request is still slow, I would check Redis and HTTP middleware latency.

If tracing is enabled, I would also check the FastAPI and database spans in Jaeger.

## Debugging Scenario 3: Provider Fallback

If fallback happens, I expect logs like:

```text
ai_router_primary_provider_failed
ai_router_fallback_attempt
ai_inference_started
ai_inference_completed
```

The primary failure log should include:

```text
category
fallback_eligible
provider
model
```

That tells me whether fallback happened because of:

```text
timeout
network
rate_limit
provider unavailable
circuit open
invalid response
```

If the category is non-fallback, the router should raise a controlled service error instead of silently sending the request somewhere else.

## Debugging Scenario 4: Cache Hit But Wrong Result

If a cached result looks wrong, I would check:

```text
cache namespace
cache schema version
prompt version
routing-policy identity
temperature
max tokens
```

The project now validates cached payload shape before returning.

If the cached value is malformed, it logs:

```text
ai_cache_invalid
```

and continues as a cache miss.

That protects the API from returning old or corrupted cache payloads.

## Production Readiness Checklist

This project is a learning implementation, not a complete production platform.

Still, it includes many production-style building blocks.

### Configuration

Implemented:

- environment-based settings
- model registry settings
- Redis host and port settings
- cache namespace and TTL settings
- OTLP endpoint setting
- body-size setting

Production improvements:

- secret manager integration
- environment-specific config validation
- startup checks for required provider routes
- typed docs for every environment variable

### Security

Implemented:

- authentication for protected routes
- role-based admin dependency
- login rate limiting
- body-size limits
- prompt character limits
- basic keyword safety filter
- safe application exception responses

Production improvements:

- stronger PII and secret detection
- prompt-injection policy
- tenant-aware AI authorization
- per-tenant provider rules
- cloud-fallback privacy controls

### Reliability

Implemented:

- async provider clients
- timeouts
- bounded retries
- circuit breakers
- provider fallback
- safe provider error categories
- graceful shutdown of long-lived clients
- validated-only cache writes

Production improvements:

- provider concurrency limits
- total inference budget across retries and fallback
- queueing or overload policy
- selected-provider usage metadata
- cost and token budgets

### Observability

Implemented:

- JSON logs
- request IDs
- HTTP metrics
- `/metrics`
- optional OpenTelemetry tracing
- Jaeger in local Docker Compose
- provider latency logs
- cache hit, miss, and invalid-cache logs
- fallback logs

Production improvements:

- AI-specific Prometheus metrics
- cache hit ratio dashboards
- provider latency dashboards
- fallback-rate dashboards
- response-validation failure alerts
- token usage and cost tracking
- distributed tracing across Redis and external HTTP clients

### AI Response Controls

Implemented:

- response parsing
- structural response validation
- suspicious output length check
- structural response scoring
- safe 502 responses for invalid AI output

Production improvements:

- schema-first model outputs
- groundedness checks
- RAG source validation
- LLM-as-judge evaluation
- human feedback loop
- model evaluation reports

## Logging Boundaries

Good observability must not become a data leak.

This project logs metadata such as:

```text
prompt_chars
raw_output_chars
provider
model
latency_seconds
category
fallback_eligible
```

It should avoid logging:

```text
raw prompts
raw model responses
API keys
bearer tokens
database URLs
Redis credentials
full provider payloads
```

There are still areas I would harden further in production.

For example, exception messages should be reviewed carefully because vendor exceptions can sometimes include request context.

The safe default is:

```text
log metadata by default
log raw content only in controlled local debugging
never log secrets
```

## What I Learned

Observability changed how I think about AI backend debugging.

Before building this project, I would have looked at a failed AI request and assumed:

```text
The model failed.
```

Now I know the failure could be:

```text
request validation
cache
routing
provider timeout
rate limit
circuit breaker
response validation
trace export
Docker networking
configuration
```

That is the real lesson.

An AI backend is not just a model call.

It is a distributed backend workflow with AI as one part of the system.

Observability is what makes that workflow understandable.

## Next

Next, I will explain configuration, middleware, and safe error handling as the backend foundation around the AI pipeline.
