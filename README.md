# AI Engineer Foundation

This project is a learning-focused backend for building production-style AI integrations with FastAPI. It combines normal application concerns such as authentication, authorization, persistence, health checks, structured logging, metrics, tracing, retries, and background audit logging with AI-specific concerns such as provider routing, prompt guardrails, response validation, caching, fallback providers, and circuit breakers.

The codebase is intentionally layered so you can study how an AI feature moves from an HTTP request, through application use cases, into a model provider, and back through validation before the client receives a response.

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Runtime Components](#runtime-components)
- [Configuration](#configuration)
- [Application Startup](#application-startup)
- [Internal Flow](#internal-flow)
- [Request Lifecycle](#request-lifecycle)
- [Sequence Diagrams](#sequence-diagrams)
- [API Examples](#api-examples)
- [AI Integration Design](#ai-integration-design)
- [Auth and Authorization](#auth-and-authorization)
- [Database and Migrations](#database-and-migrations)
- [Observability](#observability)
- [Debugging Scenarios](#debugging-scenarios)
- [Testing Notes](#testing-notes)
- [Production Considerations](#production-considerations)
- [Extension Guide](#extension-guide)
- [AI Re-Entry Guide](#ai-re-entry-guide)
- [Public Blog Series](#public-blog-series)

## Architecture

At a high level, the application follows a clean architecture style:

- API layer receives HTTP requests and translates them into use case calls.
- Dependency layer wires concrete infrastructure into abstract use cases.
- Domain layer owns business entities, repository interfaces, use cases, and exceptions.
- Repository layer implements database persistence with SQLAlchemy.
- AI application layer owns prompts, AI use cases, provider adapters, inference routing, validation, scoring, caching, and pipelines.
- Core layer owns cross-cutting behavior such as config, logging, metrics, tracing, retries, timeouts, rate limits, exception handlers, and middleware.

```mermaid
flowchart TB
    Client["HTTP client"] --> FastAPI["FastAPI app"]
    FastAPI --> Middleware["Middleware: body size, request id, metrics, rate limit"]
    Middleware --> Routers["API routers"]

    Routers --> AuthRoutes["Auth routes"]
    Routers --> HealthRoutes["Health routes"]
    Routers --> AIRoutes["AI routes"]
    Routers --> AdminRoutes["Admin routes"]

    AuthRoutes --> UserUseCases["User use cases"]
    HealthRoutes --> HealthUseCases["Health use cases"]
    AIRoutes --> AIUseCases["AI use cases"]
    AdminRoutes --> Authorization["Role authorization"]

    UserUseCases --> UserRepoPort["UserRepository interface"]
    HealthUseCases --> HealthRepoPort["HealthRepository interface"]
    UserRepoPort --> SQLAlchemyRepos["SQLAlchemy repositories"]
    HealthRepoPort --> SQLAlchemyRepos
    SQLAlchemyRepos --> Postgres["PostgreSQL"]

    AIUseCases --> SummaryService["SummaryService"]
    SummaryService --> Cache["Redis AI cache"]
    SummaryService --> InferenceRouter["InferenceRouter"]
    InferenceRouter --> ModelRegistry["ModelRegistry"]
    ModelRegistry --> Ollama["Ollama adapter"]
    ModelRegistry --> OpenAI["OpenAI adapter"]
    Ollama --> OllamaRuntime["Ollama service"]
    OpenAI --> OpenAIAPI["OpenAI API"]

    SummaryService --> ReliabilityPipeline["Response pipeline: parse, validate, guard, score"]
```

### Key Design Principles

- Routes stay thin. They parse request bodies, call use cases, and format response schemas.
- Use cases express business flow and do not depend on FastAPI request objects.
- Repository interfaces live in the domain layer; concrete SQLAlchemy implementations live outside the domain.
- AI provider calls are behind ports and adapters, so callers do not care whether the model is local Ollama or OpenAI.
- External calls are protected with retries, timeouts, circuit breakers, and provider fallback.
- AI output is treated as untrusted until parsed, validated, guarded, and scored.

## Project Structure

```text
app/
  main.py                         FastAPI app factory, lifespan, middleware, routers
  api/
    routers.py                    Central router registration
    routes/                       HTTP route modules
  application/ai/
    core/                         AI pipelines, container, parser, circuit breakers
    domain/                       AI ports, capabilities, provider enums, registry settings
    infrastructure/               OpenAI, Ollama, Redis cache, inference router
    prompts/                      Prompt builders
    schemas/                      Request/response DTOs for AI endpoints
    services/                     AI-facing application services
    usecases/                     AI use cases
    validator/                    Request safety and response validation
  core/                           Config, logging, metrics, tracing, retries, middleware
  db/                             Async SQLAlchemy engine, models
  dependencies/                   FastAPI dependency wiring
  domain/                         Entities, interfaces, use cases, domain exceptions
  repositories/                   SQLAlchemy repository implementations
  security/                       JWT, password hashing, auth dependencies, role checks
  services/                       Cross-cutting services such as audit logging
  alembic/                        Database migrations
tests/                            Test scaffolding
documents/                        Extra learning/reference documents
docker-compose.yml                Local stack: app, Postgres, Ollama, Redis, Jaeger, OTEL collector
Dockerfile                        App image and debug-aware startup
otel-config.yaml                  OpenTelemetry collector config
```

## Runtime Components

The Docker Compose stack defines these services:

- `python_ai`: FastAPI service on port `8000`; debugpy is exposed on `5678`.
- `postgres`: PostgreSQL 16 on port `5432`.
- `ollama`: Local model server on port `11434`.
- `redis`: AI response cache on port `6379`.
- `jaeger`: Trace UI on port `16686` and OTLP endpoints.
- `otel-collector`: Receives app traces and exports them to Jaeger.

Typical local startup:

```bash
docker compose up --build
```

Useful URLs:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Metrics: `http://127.0.0.1:8000/metrics`
- Jaeger UI: `http://127.0.0.1:16686`

## Public Blog Series

Publish-ready learning articles are available in [docs/blogs](./docs/blogs/README.md).

The recommended Medium publishing sequence is available in [docs/blogs/medium-series](./docs/blogs/medium-series/README.md). It starts from Python/FastAPI backend fundamentals and transitions step by step into enterprise AI backend implementation.

The series explains this project step by step for developers learning AI integration with Python and FastAPI:

0. Learning roadmap from FastAPI backend to enterprise AI backend
1. Building a production-style AI backend with FastAPI
2. Understanding the AI request lifecycle
3. Using ports and adapters for Ollama/OpenAI routing
4. Adding AI guardrails and response validation
5. Caching AI responses with Redis
6. Adding observability and production readiness

## AI Re-Entry Guide

If you return to the project after a break and need to remember how the AI integration works, start with [docs/ai-implementation-guide.md](./docs/ai-implementation-guide.md).

It explains the complete flow:

```text
Route receives -> Use case protects -> Service orchestrates -> Router selects -> Adapter calls -> Pipeline trusts
```

## Configuration

Settings are loaded by `app/core/config.py` using Pydantic Settings. The app reads `.env` locally and `.env.docker` in Docker Compose.

Required top-level settings:

```env
APP_NAME=AI Engineer
ENVIRONMENT=local
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://ai_engineer_db_user:ai_engineer_db_pass@postgres:5432/ai_engineer_db
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
LOGIN_RATE_LIMIT=5/minute
```

AI settings use nested environment variables because `env_nested_delimiter="__"` is configured:

```env
AI__PROVIDER=ollama
AI__OPENAI_API_KEY=sk-replace-me
AI__OLLAMA_BASE_URL=http://ollama:11434
AI__REDIS_HOST=redis
AI__REDIS_PORT=6379
AI__OTLP_ENDPOINT=http://otel-collector:4317
AI__TEMPERATURE=0.6
AI__MAX_TOKENS=512
AI__TIMEOUT_SECONDS=40
AI__MAX_PROMPT_LENGTH=8000
AI__HARD_PROMPT_LIMIT=20000
AI__MAX_REQUEST_BYTES=262144
AI__MODEL_REGISTRY__SUMMARIZATION__PRIMARY=ollama
AI__MODEL_REGISTRY__SUMMARIZATION__FALLBACK=openai
AI__MODEL_REGISTRY__CHAT__PRIMARY=openai
AI__MODEL_REGISTRY__CHAT__FALLBACK=ollama
```

Important behavior:

- `AIProvider.OLLAMA` maps to model `tinyllama`.
- `AIProvider.OPENAI` maps to model `gpt-4.1-mini`.
- `AISettings.validate_ai_settings()` overwrites `model_name` with the provider default.
- OpenAI API keys are required only when OpenAI is selected directly or appears in a configured model route.
- `ModelRegistry.load()` expects `AI__MODEL_REGISTRY__SUMMARIZATION__PRIMARY` to exist. Without model registry config, AI routing returns a controlled service error when it looks up a capability.
- Redis host and port are configurable through `AI__REDIS_HOST` and `AI__REDIS_PORT`.
- Tracing is enabled only when `AI__OTLP_ENDPOINT` is configured.

## Application Startup

`app/main.py` exposes `create_app()` and the ASGI variable `app`.

Startup order:

1. Load settings.
2. Configure JSON logging.
3. Create the FastAPI app with lifespan support.
4. Configure OpenTelemetry tracing.
5. Register rate limiting, metrics, request ID, and body size middleware.
6. Include all routers.
7. Register global exception handlers.
8. During lifespan startup, create `ServiceContainer`, load model routing, and initialize database tables.
9. During lifespan shutdown, close Ollama HTTP client, model registry adapters, and Redis.

```mermaid
sequenceDiagram
    participant Uvicorn
    participant App as FastAPI app
    participant Container as ServiceContainer
    participant Registry as ModelRegistry
    participant DB as Database
    participant Redis

    Uvicorn->>App: import app.main:app
    App->>App: create_app()
    Uvicorn->>App: lifespan startup
    App->>Container: ServiceContainer(settings)
    Container->>Registry: register OpenAI and Ollama adapters
    Container->>Redis: create async Redis client
    App->>Container: startup()
    Container->>Registry: load model routes from settings
    App->>DB: Base.metadata.create_all()
    Uvicorn->>App: serve requests
    Uvicorn->>App: lifespan shutdown
    App->>Container: shutdown()
```

## Internal Flow

### Layer Responsibilities

| Layer | Main files | Responsibility |
| --- | --- | --- |
| API | `app/routers/routes/*.py` | HTTP endpoint definitions, request/response schemas, dependency injection |
| Dependencies | `app/dependencies/*.py` | Compose use cases, repositories, services, and AI container components |
| Domain | `app/domain/**` | Entities, business use cases, repository interfaces, domain exceptions |
| Repositories | `app/repositories/*.py` | SQLAlchemy persistence implementation |
| AI core | `app/application/ai/core/*.py` | Pipelines, parser, registry, container, circuit breakers |
| AI infra | `app/application/ai/infrastructure/*.py` | OpenAI/Ollama/Redis implementations and provider routing |
| Security | `app/security/*.py` | JWT encode/decode, password hashing, auth dependency, role checks |
| Core | `app/core/*.py` | Config, observability, middleware, retry, timeout, error mapping |

### Dependency Injection Pattern

The code uses FastAPI dependencies as the composition root:

```python
def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(settings),
) -> UserRepository:
    return SQLAlchemyUserRepository(session, settings)


def get_register_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repo)
```

This keeps route handlers independent from concrete database implementations.

## Request Lifecycle

Every HTTP request passes through the application in this order:

1. Client sends request.
2. `BodySizeLimitMiddleware` rejects oversized requests using `Content-Length`.
3. `RequestIDMiddleware` accepts or creates `X-Request-ID` and stores it in a context variable.
4. `MetricsMiddleware` records request count, latency, and unhandled errors.
5. SlowAPI applies route-level rate limits where configured.
6. FastAPI validates the request body with Pydantic schemas.
7. Route dependencies resolve sessions, repositories, use cases, security context, and services.
8. Use case executes business logic.
9. Repositories, AI providers, Redis, or other external dependencies are called as needed.
10. Domain exceptions are translated into consistent HTTP JSON responses.
11. Response is returned with `X-Request-ID`.
12. Background tasks such as audit logging run after response scheduling.

```mermaid
flowchart LR
    Client --> BodyLimit["Body size limit"]
    BodyLimit --> RequestID["Request ID context"]
    RequestID --> Metrics["Prometheus metrics"]
    Metrics --> RateLimit["SlowAPI rate limit"]
    RateLimit --> Validation["Pydantic validation"]
    Validation --> Route["Route handler"]
    Route --> Dependencies["FastAPI dependencies"]
    Dependencies --> UseCase["Use case"]
    UseCase --> Infra["DB, Redis, AI providers"]
    Infra --> Handler["Exception or response mapping"]
    Handler --> Client
```

## Sequence Diagrams

### User Registration

Endpoint: `POST /auth/register`

```mermaid
sequenceDiagram
    participant Client
    participant Route as Auth route
    participant UseCase as RegisterUserUseCase
    participant Repo as SQLAlchemyUserRepository
    participant DB as PostgreSQL
    participant Audit as AuditService

    Client->>Route: POST /auth/register
    Route->>UseCase: execute(email, password)
    UseCase->>Repo: get_by_email(email)
    Repo->>DB: SELECT users WHERE email = ?
    DB-->>Repo: user or null
    alt user exists
        UseCase-->>Route: UserAlreadyExistsError
        Route-->>Client: 409 USER_ALREADY_EXISTS
    else new user
        UseCase->>UseCase: hash password and create domain User
        UseCase->>Repo: create(user, password_hash)
        Repo->>DB: INSERT users
        DB-->>Repo: created row
        Repo-->>UseCase: domain User
        UseCase-->>Route: User
        Route->>Audit: schedule USER_REGISTERED background task
        Route-->>Client: 201 UserResponse
    end
```

### User Login and Protected Request

Endpoints: `POST /auth/login`, then `GET /auth/me`

```mermaid
sequenceDiagram
    participant Client
    participant LoginRoute as Login route
    participant LoginUseCase as LoginUserUseCase
    participant Repo as UserRepository
    participant JWT as JWT service
    participant ProtectedRoute as Protected route
    participant Security as Security dependency

    Client->>LoginRoute: POST /auth/login
    LoginRoute->>LoginUseCase: execute(email, password)
    LoginUseCase->>Repo: get_by_email(email)
    Repo-->>LoginUseCase: User with password_hash
    LoginUseCase->>LoginUseCase: verify_password()
    LoginRoute->>JWT: create_access_token(user)
    LoginRoute-->>Client: access_token

    Client->>ProtectedRoute: GET /auth/me with Authorization header
    ProtectedRoute->>Security: get_current_user()
    Security->>JWT: decode_token()
    Security->>Repo: get user by sub
    Repo-->>Security: User
    ProtectedRoute-->>Client: UserResponse
```

### AI Summarization

Endpoint: `POST /ai/summarize`

```mermaid
sequenceDiagram
    participant Client
    participant Route as AI route
    participant UseCase as SummarizeTextUseCase
    participant Safety as AISafetyFilter
    participant Guardrails as AIGuardrails
    participant Service as SummaryService
    participant Cache as RedisAIResponseCache
    participant Router as InferenceRouter
    participant Registry as ModelRegistry
    participant Provider as Ollama/OpenAI adapter
    participant Pipeline as SummarizationPipeline

    Client->>Route: POST /ai/summarize
    Route->>UseCase: execute(text)
    UseCase->>Safety: check(text)
    Safety-->>UseCase: ok or validation error
    UseCase->>Guardrails: validate_prompt(text)
    Guardrails-->>UseCase: sanitized text
    UseCase->>Service: summarize(text)
    Service->>Service: build SummaryPrompt
    Service->>Cache: build_key() and get()
    alt cache hit
        Cache-->>Service: JSON bullets
        Service-->>Route: bullets
    else cache miss
        Service->>Router: generate(capability, prompt)
        Router->>Registry: get_primary(SUMMARIZATION)
        Registry-->>Router: provider adapter
        Router->>Provider: generate(prompt)
        alt primary fails with AIProviderError
            Router->>Registry: get_fallback(SUMMARIZATION)
            Router->>Provider: generate(prompt)
        end
        Provider-->>Service: raw model text
        Service->>Pipeline: run(raw_output)
        Pipeline->>Pipeline: validate, parse, validate bullets, guard, score
        Pipeline-->>Service: bullets and score
        Service->>Cache: set(key, bullets, ttl=3600)
        Service-->>Route: bullets
    end
    Route-->>Client: SummaryResponse
```

### Health Checks

```mermaid
flowchart TB
    Live["GET /health/live"] --> LiveUseCase["LivenessCheckUseCase"]
    LiveUseCase --> Alive["status: alive"]

    Ready["GET /health/ready"] --> ReadyUseCase["ReadinessCheckUseCase"]
    ReadyUseCase --> HealthRepo["HealthRepositoryImpl"]
    HealthRepo --> DB["health_status table"]
    ReadyUseCase --> ReadyResponse["status: ready"]

    Deep["GET /health/deep"] --> DeepUseCase["DeepHealthCheckUseCase"]
    DeepUseCase --> HealthRepo
    DeepUseCase --> DeepResponse["database and service statuses"]
```

## API Examples

### Health

```bash
curl http://127.0.0.1:8000/health/
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
curl http://127.0.0.1:8000/health/deep
```

### Register

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "learner@example.com",
    "password": "strong-password"
  }'
```

Expected response:

```json
{
  "id": "8e9fb8e7-daf8-46b2-8f0d-3d93a77e7617",
  "email": "learner@example.com",
  "is_active": true,
  "role": "user"
}
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "learner@example.com",
    "password": "strong-password"
  }'
```

Expected response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Current User

```bash
TOKEN="paste-token-here"

curl http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### AI Summarization

```bash
curl -X POST http://127.0.0.1:8000/ai/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "FastAPI is a modern Python web framework. It supports async request handling, dependency injection, Pydantic validation, automatic OpenAPI docs, and strong editor support."
  }'
```

Expected response shape:

```json
{
  "bullets": [
    "FastAPI is a modern Python framework for building APIs.",
    "It supports async request handling and dependency injection.",
    "It uses Pydantic for validation and OpenAPI documentation."
  ]
}
```

## AI Integration Design

The AI feature is structured around ports, adapters, routing, and a reliability pipeline.

### Request Validation

`SummarizeTextUseCase` applies two request-side protections:

- `AISafetyFilter` rejects sensitive terms such as `credit card`, `cvv`, `password`, and `ssn`.
- `AIGuardrails` rejects empty input, hard rejects very large prompts, detects likely binary input, sanitizes control characters, normalizes whitespace, and soft-truncates long prompts.

### Prompt Construction

`SummaryPrompt` builds the final model prompt. The prompt text is part of the cache key, which means prompt changes naturally invalidate old cache entries.

### Caching

`RedisAIResponseCache` hashes these fields into a stable cache key:

- capability
- prompt
- model
- temperature
- max tokens

Cached summarization responses are stored for one hour.

### Provider Routing

`InferenceRouter` asks `ModelRegistry` for a primary adapter and optional fallback adapter for the requested capability.

For summarization, a typical route is:

```env
AI__MODEL_REGISTRY__SUMMARIZATION__PRIMARY=ollama
AI__MODEL_REGISTRY__SUMMARIZATION__FALLBACK=openai
```

Provider failures must be raised as `AIProviderError` for fallback to activate.

### Provider Adapters

`OllamaAdapter` calls:

```text
POST /api/generate
```

with `model`, `prompt`, `temperature`, and `num_predict`.

`OpenAIAdapter` calls the OpenAI Responses API through `AsyncOpenAI.responses.create()`.

Both adapters:

- log inference start and completion
- normalize provider errors into `AIProviderError`
- use retry via `infra_retry()`
- use a circuit breaker to stop repeatedly calling failing providers
- reject empty model output

### Response Reliability Pipeline

`SummarizationPipeline.run()` performs:

1. Raw response validation.
2. Bullet parsing.
3. Structured bullet validation.
4. Hallucination guard checks.
5. Quality scoring.

The current scorer is intentionally simple. It rewards average bullet length above 60 characters and at least five bullets. `SummaryService` rejects outputs below `0.6`.

## Auth and Authorization

Authentication uses JWT bearer tokens.

- `POST /auth/register` creates a user with hashed password and default role `user`.
- `POST /auth/login` verifies the password and returns a JWT.
- `get_token_payload()` decodes the JWT from the Authorization header.
- `get_current_user()` loads the user from the repository using the token subject.
- `get_current_active_user()` rejects inactive users.
- `require_role(UserRole.ADMIN)` protects admin-only endpoints such as `/admin/dashboard` and `/auth/users`.

JWT payload shape:

```json
{
  "sub": "user-uuid",
  "role": "user",
  "exp": 1760000000
}
```

Passwords are hashed through `app/security/password.py` using Passlib/bcrypt.

## Database and Migrations

The application uses async SQLAlchemy:

- Engine: `create_async_engine(settings.database_url)`
- Session factory: `async_sessionmaker`
- Base metadata: `declarative_base()`

Current ORM models:

- `UserORM` in `app/db/models/user_orm.py`
- `AuditORM` in `app/db/models/audit_orm.py`
- `HealthStatus` in `app/db/models/health.py`

The app also calls `Base.metadata.create_all()` during startup. Alembic migrations live under `app/alembic/versions`.

Common migration commands:

```bash
alembic -c app/alembic.ini revision --autogenerate -m "describe change"
alembic -c app/alembic.ini upgrade head
alembic -c app/alembic.ini downgrade -1
```

For production, prefer migrations as the source of schema changes and avoid relying on `create_all()` to modify managed databases.

## Observability

### Structured Logging

`app/core/logging.py` configures JSON logs to stdout.

Logs include:

- timestamp
- level
- logger
- message
- request ID when available
- custom `extra` fields such as event names, user IDs, provider names, model names, and latency

Example event names used in the code:

- `service_startup`
- `user_register_attempt`
- `user_register_conflict`
- `user_login_success`
- `ai_cache_hit`
- `ai_cache_miss`
- `ai_inference_started`
- `ai_inference_completed`
- `audit_log_success`

### Request IDs

`RequestIDMiddleware` reads `X-Request-ID` or creates a UUID. The ID is stored in a context variable and returned on the response as `X-Request-ID`.

Use it while debugging:

```bash
curl http://127.0.0.1:8000/health/live \
  -H "X-Request-ID: local-debug-001"
```

Then search logs for `local-debug-001`.

### Prometheus Metrics

`MetricsMiddleware` records:

- `http_requests_total{method,path,status}`
- `http_request_duration_seconds{method,path}`
- `http_request_errors_total{method,path}`

Scrape endpoint:

```bash
curl http://127.0.0.1:8000/metrics
```

### OpenTelemetry Tracing

When `AI__OTLP_ENDPOINT` is configured, `app/core/tracing.py` instruments FastAPI and SQLAlchemy and exports OTLP spans to that endpoint. In Docker Compose this is:

```text
http://otel-collector:4317
```

In Docker Compose, the OTEL collector forwards traces to Jaeger. Open:

```text
http://127.0.0.1:16686
```

Then search for service name `AI Engineer`.

## Debugging Scenarios

### App Fails on Startup with Missing Settings

Symptoms:

- Uvicorn exits immediately.
- Pydantic validation error mentions `database_url`, `jwt_secret_key`, or `ai`.

Likely causes:

- `.env` or `.env.docker` missing required values.
- Nested AI env names are not using double underscores.

Check:

```bash
docker compose logs python_ai
```

Fix:

- Add required config keys.
- Ensure AI nested keys follow names like `AI__MODEL_REGISTRY__SUMMARIZATION__PRIMARY`.

### AI Summarization Fails Before Provider Call

Symptoms:

- Response is `400`, `413`, or `422`.
- Logs mention sensitive data, binary input, or prompt size.

Relevant files:

- `app/application/ai/usecases/summarize_text.py`
- `app/application/ai/validator/request/ai_safety.py`
- `app/application/ai/validator/request/ai_guardrails.py`
- `app/core/middleware/body_size.py`

Common causes:

- Request body larger than `AI__MAX_REQUEST_BYTES`.
- Prompt larger than `AI__HARD_PROMPT_LIMIT`.
- Input contains blocked sensitive terms.
- Input contains a high ratio of non-printable characters.

### AI Router Cannot Select a Provider

Symptoms:

- `POST /ai/summarize` returns `500`.
- Logs include `model_registry_not_configured` during startup or a key lookup failure when summarization runs.

Relevant files:

- `app/core/model_registry.py`
- `app/application/ai/infrastructure/ai_inference_port.py`
- `app/core/config.py`

Fix:

```env
AI__MODEL_REGISTRY__SUMMARIZATION__PRIMARY=ollama
AI__MODEL_REGISTRY__SUMMARIZATION__FALLBACK=openai
```

### Ollama Is Unavailable

Symptoms:

- Logs show `ai_transport_error`, `ai_timeout`, or `ai_provider_error` with provider `ollama`.
- If fallback is configured, the request may still succeed through OpenAI.
- If no fallback exists or fallback also fails, client gets an AI/service error.

Check:

```bash
docker compose ps
docker compose logs ollama
curl http://127.0.0.1:11434/api/tags
```

Fix:

- Start the `ollama` container.
- Pull the expected model into Ollama if needed.
- Confirm `AI__OLLAMA_BASE_URL=http://ollama:11434` inside Docker.

### OpenAI Calls Fail

Symptoms:

- Logs show provider `openai` with `ai_rate_limited`, `ai_timeout`, or `ai_provider_error`.
- Response may fall back to Ollama if configured.

Check:

- `AI__OPENAI_API_KEY` is set.
- The key starts with `sk-`.
- Network egress is available from the running environment.
- Rate limits or quotas are not exhausted.

### Redis Cache Fails Locally

Symptoms:

- Cache operations fail when running the app directly on the host.
- Docker Compose works, but local `uvicorn app.main:app` fails to resolve `redis`.

Cause:

- `ServiceContainer` creates Redis with `host="redis"`, which is the Docker service name.

Fix options:

- Run through Docker Compose.
- Make Redis host configurable, then use `localhost` for host-based local development.

### Low Quality AI Output

Symptoms:

- Response returns an AI validation error.
- Logs show validation succeeded at provider level but `SummaryService` rejects the score.

Relevant files:

- `app/application/ai/core/summarization_pipeline.py`
- `app/application/ai/validator/response/response_scorer.py`
- `app/application/ai/validator/response/response_validator.py`
- `app/application/ai/validator/response/hallucination_guard.py`

Common causes:

- Model returned too few bullets.
- Bullets are very short.
- Prompt did not strongly request bullet formatting.

### Protected Endpoint Returns 401

Symptoms:

- `/auth/me`, `/auth/users`, or `/admin/dashboard` returns unauthorized.

Check:

- Header format is `Authorization: Bearer <token>`.
- Token has not expired.
- `JWT_SECRET_KEY` matches the process that created the token.
- User still exists and is active.

Relevant files:

- `app/security/security.py`
- `app/security/jwt.py`
- `app/security/dependencies.py`

### Admin Endpoint Returns 403

Symptoms:

- Authenticated request succeeds elsewhere but fails on admin route.

Cause:

- User role is not `admin`.

Relevant files:

- `app/security/authorization.py`
- `app/domain/entities/user_role.py`
- `app/routers/routes/admin.py`

### Audit Logging Fails Silently

Symptoms:

- User registration or login succeeds.
- Audit table does not receive an event.
- Logs contain `audit_log_failed`.

Design note:

- `AuditService.log_event()` catches and logs exceptions so audit failures do not break the main user flow.
- Audit repository uses its own session factory because background tasks should not depend on the request session lifecycle.

## Testing Notes

Install development dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

Current note: `tests/api/test_health.py` appears to target an older dependency name and older `/health` behavior. The current protected `/health` route requires authentication and `app.dependencies.deps` no longer exports `health_service`. Recommended test updates:

- Test public health endpoints: `/health/`, `/health/live`, `/health/ready`, `/health/deep`.
- Override repository dependencies from `app.dependencies.repositories`, not a removed `health_service`.
- For protected `/health`, create a test user and token or override `get_current_user`.
- Add AI tests that override `get_summarize_use_case` or the container inference adapter to avoid real model calls.

Example AI unit test shape:

```python
class FakeSummaryUseCase:
    async def execute(self, text: str) -> list[str]:
        return ["FastAPI handles requests.", "The AI layer summarizes text."]


def override_summarize_use_case():
    return FakeSummaryUseCase()


app.dependency_overrides[get_summarize_use_case] = override_summarize_use_case
```

## Production Considerations

### Configuration and Secrets

- Never commit real `.env` files or API keys.
- Use a secret manager for `JWT_SECRET_KEY`, database credentials, and OpenAI keys.
- Validate startup config before accepting traffic.
- Keep Redis host, OTLP endpoint, and provider settings environment-driven.

### Database

- Use Alembic migrations in deployment pipelines.
- Avoid relying on `Base.metadata.create_all()` in production.
- Add connection pool sizing based on expected concurrency.
- Add indexes for common query paths, especially `users.email`.

### Security

- Use a long random `JWT_SECRET_KEY`.
- Rotate secrets safely.
- Enforce HTTPS at the ingress layer.
- Consider refresh tokens or shorter-lived access tokens for real products.
- Store admin role changes behind auditable workflows.
- Avoid logging sensitive prompt content or credentials.

### AI Safety and Reliability

- Treat prompts and model outputs as untrusted data.
- Expand safety filters beyond static blocked terms for sensitive data detection.
- Add model-specific prompt versions.
- Track prompt version, model, provider, latency, and validation failures.
- Add richer response evaluation for important AI workflows.
- Add rate limits specific to expensive AI endpoints.
- Add budget controls per user or API key.
- Add fallback policies per capability rather than one global provider assumption.

### Caching

- Include prompt version in the cache key if prompt builders evolve frequently.
- Consider different TTLs per capability.
- Add cache metrics for hit rate, miss rate, and Redis errors.
- Decide whether user-specific context should be part of cache keys before caching personalized AI output.

### Observability

- Send logs to a centralized log system.
- Scrape Prometheus metrics from `/metrics`.
- Ensure OTLP endpoint is configurable per environment.
- Add provider-level metrics such as AI latency, provider errors, fallback count, and circuit breaker state.
- Use request IDs across API gateway, app logs, and traces.

### Deployment

- Disable `--reload` in production.
- Run database migrations before starting the app.
- Add readiness probes that fail when critical dependencies are unavailable.
- Add liveness probes that only check process health.
- Configure worker count and timeouts based on model latency and DB pool size.
- Consider separating AI workloads from auth/user APIs if model calls become slow or expensive.

## Extension Guide

### Add a New AI Capability

1. Add a value to `AICapability`.
2. Create a request/response schema in `app/application/ai/schemas`.
3. Create a prompt builder in `app/application/ai/prompts`.
4. Create a use case in `app/application/ai/usecases`.
5. Create or reuse a pipeline in `app/application/ai/core`.
6. Register the pipeline in `ServiceContainer`.
7. Add model routing config to `ModelRegistrySettings`.
8. Add a route under `app/routers/routes`.
9. Wire dependencies in `app/dependencies/ai_dependencies.py`.
10. Add tests with fake inference adapters.

### Add a New AI Provider

1. Add the provider to `AIProvider`.
2. Implement `AIModelPort`.
3. Normalize provider failures into `AIProviderError`.
4. Add retry, timeout, and circuit breaker protection.
5. Register the adapter in `ServiceContainer`.
6. Add model routing config for the target capabilities.

### Add a New Protected Endpoint

1. Define request/response schemas.
2. Add a domain use case.
3. Add or reuse repository interfaces.
4. Implement repository behavior.
5. Wire dependencies.
6. Add route with `Depends(get_current_user)` or `Depends(require_role(...))`.
7. Add tests for success, unauthorized, forbidden, and domain errors.

## Learning Path

For studying the project, read in this order:

1. `app/main.py` to understand app setup and middleware.
2. `app/routers/routers.py` and `app/routers/routes/*.py` to understand HTTP surface area.
3. `app/dependencies/*.py` to understand dependency injection.
4. `app/domain/use_cases/**` to understand business flow.
5. `app/repositories/*.py` and `app/db/models/*.py` to understand persistence.
6. `app/application/ai/usecases/summarize_text.py` and `app/application/ai/services/summary_service.py` to understand the AI request flow.
7. `app/application/ai/core/container.py` to understand long-lived clients and runtime wiring.
8. `app/application/ai/infrastructure/*.py` to understand provider adapters, fallback, Redis cache, and external calls.
9. `app/core/*.py` to understand production support systems.

## Known Maintenance Notes

- Several comments contain visual markers from learning notes; consider standardizing comments as the code matures.
- `Base.metadata.create_all()` is convenient locally, but migrations should own schema changes in production.
