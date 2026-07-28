# 06 - Observability and Production Readiness for AI Backends

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


When an AI endpoint fails, you need to answer practical questions quickly:

- Did the request reach the API?
- Was the prompt rejected?
- Was the response served from cache?
- Which provider was called?
- How long did the model take?
- Did fallback happen?
- Did response validation fail?
- Did tracing export correctly?

This is why AI backends need observability.

## Observability in This Project

The project includes:

- structured JSON logging
- request IDs
- Prometheus metrics
- OpenTelemetry tracing
- Jaeger
- provider latency logs
- cache hit/miss logs
- domain-level exception mapping

These pieces make the system easier to debug.

## Structured Logging

Logging is configured in:

```text
app/core/logging.py
```

Logs are JSON formatted, which makes them easier to search and ship to log platforms.

Example AI inference log:

```json
{
  "level": "INFO",
  "logger": "app.application.ai.infrastructure.ollama_adapter",
  "message": "ai_inference_completed",
  "provider": "ollama",
  "model": "tinyllama",
  "latency_seconds": 12.39,
  "request_id": "98754ae8-41d0-4a4f-aaae-b194fd28831c"
}
```

This tells you:

- which provider ran
- which model ran
- how long it took
- which request caused it

## Request IDs

Request IDs are handled in:

```text
app/core/middleware/request_id.py
```

The middleware:

- reads an incoming `X-Request-ID`
- creates one if missing
- stores it in context
- adds it to response headers
- includes it in logs

This lets you trace a single request across multiple log lines.

## Metrics

Prometheus metrics are defined in:

```text
app/core/metrics.py
app/core/middleware/metrics_middleware.py
```

The app records:

- request count
- request latency
- request errors

Metrics endpoint:

```http
GET /metrics
```

For AI-specific production metrics, add:

- provider latency
- provider error count
- fallback count
- cache hit/miss count
- response validation failure count
- token usage
- cost estimates

## Tracing

Tracing is configured in:

```text
app/core/tracing.py
```

When `AI__OTLP_ENDPOINT` is configured, the app exports traces to the OpenTelemetry Collector.

In Docker Compose:

```env
AI__OTLP_ENDPOINT=http://otel-collector:4317
```

The collector sends traces to Jaeger.

Jaeger UI:

```text
http://127.0.0.1:16686
```

Tracing is useful when one request touches:

- FastAPI
- database
- Redis
- AI provider
- background tasks

## Debugging Example: AI Request Works but Tracing Fails

You may see logs like:

```text
ai_inference_completed
ai_inference_response_received
Failed to export traces to otel-collector:4317
```

This means the AI request worked, but tracing export failed.

The model call and tracing pipeline are separate concerns.

Check:

```bash
docker compose ps
docker compose logs otel-collector
docker compose logs jaeger
```

Also confirm that Compose defines:

- `jaeger`
- `otel-collector`
- `AI__OTLP_ENDPOINT=http://otel-collector:4317`

## Production Readiness Checklist

Before deploying an AI backend, review these areas.

### Configuration

- no real secrets committed
- all provider keys from secret manager
- Redis host configurable
- OTLP endpoint configurable
- model routes configurable
- environment-specific config separated

### Security

- HTTPS at ingress
- strong JWT secret
- request body size limits
- prompt size limits
- sensitive data filtering
- authentication on private endpoints
- role checks for admin endpoints

### Reliability

- provider retries
- provider timeouts
- circuit breakers
- fallback provider
- graceful provider errors
- validated AI responses
- cache only trusted output

### Observability

- request IDs in logs
- provider latency logs
- cache hit/miss logs
- Prometheus metrics
- OpenTelemetry traces
- alerting on provider errors
- alerting on latency spikes

### Testing

- unit tests for guardrails
- unit tests for response pipelines
- tests for cache hit/miss behavior
- tests for provider fallback
- tests for missing provider config
- tests for protected endpoints

## What Makes AI Backends Different?

Traditional APIs usually depend on deterministic services.

AI providers are different:

- output can vary
- latency can be high
- cost matters
- failures can be partial
- response shape is not guaranteed
- model behavior can change

That is why AI backends need extra care around validation, fallback, observability, and cost control.

## Final Thought

Production readiness is not one feature.

It is the combination of many small engineering decisions:

- clean boundaries
- safe inputs
- trusted outputs
- clear logs
- useful metrics
- provider resilience
- predictable failures

That is what turns an AI demo into an AI backend.
