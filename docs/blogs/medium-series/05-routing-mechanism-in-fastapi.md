# 05 - Creating a Clean Routing Mechanism in FastAPI

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)

Routing is where HTTP requests enter the application.

In a small FastAPI project, it is common to keep every route in `main.py`.

That is fine for learning the first endpoint.

But once the backend starts adding authentication, health checks, admin APIs, metrics, and AI capabilities, route organization becomes important.

In this project, routing helped me understand one important backend idea:

```text
The route should describe the HTTP boundary.
The application layer should own the workflow.
```

## Routing Structure In This Project

The application entry point is:

```text
app/main.py
```

The route registration file is:

```text
app/routers/routers.py
```

Feature route modules live under:

```text
app/routers/routes/
```

The current routing tree is:

```text
app/
├── main.py
├── routers/
│   ├── routers.py
│   └── routes/
│       ├── admin.py
│       ├── ai.py
│       ├── auth.py
│       ├── health.py
│       └── metrics.py
```

Each file groups routes by feature or operational concern.

This makes the project easier to navigate as endpoints, features, and contributors increase.

## How Routers Are Registered

This project does not currently use a parent `/api` or `/api/v1` router.

Instead, each feature router is included directly into the FastAPI application from:

```text
app/routers/routers.py
```

The registration flow is:

```text
feature routers
-> app/routers/routers.py
-> FastAPI app in app/main.py
```

The code looks like this:

```python
def addRouters(app: FastAPI) -> None:
    routers = [
        health_public_router,
        health_protected_router,
        metrics_router,
        auth_public_router,
        auth_protected_router,
        admin_router,
        ai_router,
    ]

    for router in routers:
        app.include_router(router)
```

`app/main.py` calls this registration function when creating the FastAPI app.

That keeps `main.py` focused on application assembly:

- logging
- tracing
- middleware
- router registration
- exception handlers
- lifespan startup and shutdown

## Current Route Inventory

These are the currently registered application routes, excluding FastAPI's built-in documentation routes.

```text
GET  /health/
GET  /health/live
GET  /health/ready
GET  /health/deep
GET  /health
GET  /metrics
POST /auth/register
POST /auth/login
GET  /auth/me
GET  /auth/users
GET  /admin/dashboard
POST /ai/summarize
```

There is no `/api/v1` prefix yet.

A version prefix such as `/api/v1` can be introduced later when backward-compatible API evolution becomes necessary.

## Route Groups

The project currently uses these route modules:

```text
app/routers/routes/auth.py
```

Handles registration, login, current-user lookup, and user listing.

```text
app/routers/routes/ai.py
```

Handles the summarization HTTP endpoint.

```text
app/routers/routes/health.py
```

Handles public liveness/readiness/deep health checks and one authenticated health endpoint.

```text
app/routers/routes/admin.py
```

Handles the admin dashboard endpoint.

```text
app/routers/routes/metrics.py
```

Exposes Prometheus metrics at `/metrics`.

## Prefixes And Tags

FastAPI routers can define URL prefixes and OpenAPI tags.

The AI router is:

```python
public_router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)
```

That produces:

```text
POST /ai/summarize
```

The auth routers use:

```text
prefix="/auth"
tags=["auth"]
```

The admin router uses:

```text
prefix="/admin"
tags=["admin"]
```

The public health router uses:

```text
prefix="/health"
tags=["health"]
```

Tags are useful because they group endpoints in the generated OpenAPI schema and Swagger UI.

One detail I noticed: the protected `/health` route and `/metrics` route are registered without explicit tags today. That works, but adding tags later would make the generated API documentation more consistent.

## Public, Protected, And Role-Protected Routes

This project separates routes by access level.

Current public routes:

```text
GET  /health/
GET  /health/live
GET  /health/ready
GET  /health/deep
GET  /metrics
POST /auth/register
POST /auth/login
POST /ai/summarize
```

Current authenticated routes:

```text
GET /auth/me
GET /health
```

Current role-protected routes:

```text
GET /auth/users        requires ADMIN
GET /admin/dashboard   requires ADMIN
```

The summarization endpoint is currently public for learning and local development.

For production, I would normally add one or more controls:

- JWT authentication
- API-key authentication
- rate limits
- usage quotas
- model-provider cost controls
- model concurrency limits

This is important because AI endpoints can be expensive and slow compared to normal CRUD endpoints.

## File Separation Is Not Security

One important correction I learned:

> Separate routers make security policies easier to organize, but folder separation does not itself enforce security.

Security is enforced through FastAPI dependencies and application logic.

For example, protected auth routes use a router-level dependency:

```python
protected_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(get_current_active_user)],
)
```

The `/auth/users` route also adds an admin role requirement:

```python
dependencies=[Depends(require_role(UserRole.ADMIN))]
```

The admin dashboard uses role protection at the endpoint parameter level:

```python
async def admin_dashboard(
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    return {"message": "Welcome, admin"}
```

So the real security boundary is dependency execution, not the folder name.

## Dependency Injection At Route Level

Routes receive use cases and security context through FastAPI dependencies.

The AI route uses:

```python
use_case: SummarizeTextUseCase = Depends(get_summarize_use_case)
```

The dependency graph is:

```text
route
-> get_summarize_use_case
-> get_summary_service
-> get_container
-> request.app.state.container
```

The long-lived AI container is created during application lifespan startup.

That container owns reusable resources such as:

- Ollama async HTTP client
- optional OpenAI async client
- Redis client
- model registry
- inference router
- pipeline registry

The route does not create those clients directly.

FastAPI resolves the endpoint's dependency graph and supplies the objects and request-scoped resources required by the route.

FastAPI also caches dependency results within a single request by default unless `use_cache=False` is used.

That means a dependency can be reused within the same request without recomputing it unnecessarily.

## Request-Scoped And Application-Scoped Dependencies

Not every dependency has the same lifecycle.

Request-scoped examples:

- database session
- current user
- request metadata
- use-case object

Application-scoped examples:

- AI service container
- reusable provider clients
- Redis client
- model registry
- inference router

This distinction matters.

A database session should be request-scoped or unit-of-work scoped.

An HTTP client or Redis client should usually be application-scoped and closed during shutdown.

## AI Route Example

The AI route lives in:

```text
app/routers/routes/ai.py
```

Its request and response schemas live in:

```text
app/application/ai/schemas/ai_summary.py
```

The request model is:

```python
class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=1)
```

The response model is:

```python
class SummaryResponse(BaseModel):
    bullets: list[str]
```

The route declares the response contract:

```python
@public_router.post("/summarize", response_model=SummaryResponse)
async def summarize(
    request: SummaryRequest,
    use_case: SummarizeTextUseCase = Depends(get_summarize_use_case),
):
    bullets = await use_case.execute(request.text)
    return SummaryResponse(bullets=bullets)
```

The route owns HTTP concerns:

- URL path
- HTTP method
- request schema
- response schema
- dependency declaration
- mapping application output to HTTP output

The route does not contain:

- provider selection
- Ollama calls
- OpenAI calls
- Redis cache logic
- fallback logic
- prompt construction
- response parsing
- response validation

That work belongs below the HTTP layer.

## Thin Routes Do Not Mean One-Line Routes

A route stays thin by focusing on HTTP concerns, not by being limited to a fixed number of lines.

A route may legitimately handle:

- path parameters
- query parameters
- headers
- cookies
- request schemas
- response schemas
- status codes
- authentication dependencies
- OpenAPI metadata
- response headers

A route should generally avoid owning:

- business rules
- SQLAlchemy queries
- cache strategy
- provider selection
- prompt construction
- retry policy
- fallback policy
- model-response parsing
- transaction orchestration

This separation keeps the routing layer readable without making it artificially tiny.

## Responsibility Model

The routing layer fits into the larger architecture like this:

```text
Route
-> translates HTTP input and output

Use case
-> coordinates one application operation

Service
-> provides reusable workflow or business behavior

Port or interface
-> defines what capability the application needs

Adapter
-> communicates with external infrastructure
```

For summarization, the flow is:

```text
HTTP route
-> accepts and validates SummaryRequest
-> calls SummarizeTextUseCase
-> use case coordinates the summarization operation
-> SummaryService runs the summarization workflow
-> InferenceRouter selects the model provider
-> OllamaAdapter or OpenAIAdapter communicates with the provider
```

The route knows the HTTP contract.

The use case knows the application action.

The service knows the reusable workflow.

The adapter knows the external system.

## Centralized Exception Handling

Routes in this project do not repeat large `try/except` blocks for every domain failure.

Application exceptions are mapped through centralized FastAPI exception handlers.

The registration happens in:

```text
app/core/exception_registry.py
```

The handlers live in:

```text
app/core/exception_handlers.py
```

The flow is:

```text
domain or application exception
-> centralized FastAPI exception handler
-> standardized HTTP JSON response
```

This keeps route handlers focused on HTTP translation instead of repeated error formatting.

## Health And Metrics Routes

Health routes live in:

```text
app/routers/routes/health.py
```

Public health endpoints:

```text
GET /health/
GET /health/live
GET /health/ready
GET /health/deep
```

There is also an authenticated health endpoint:

```text
GET /health
```

Metrics live in:

```text
app/routers/routes/metrics.py
```

The metrics endpoint is:

```text
GET /metrics
```

It returns Prometheus metrics using:

```python
generate_latest()
```

In production, metrics and operational endpoints are often restricted at the network, gateway, or deployment level even if the application route itself is public.

## What I Learned

Routing is not just URL mapping.

It defines the external HTTP contract:

- method and URL
- request schema
- response schema
- status code
- authentication requirement
- authorization requirement
- error contract
- OpenAPI documentation

The route should answer:

> What HTTP endpoint is this?

The use case should answer:

> What application operation happens?

The service should answer:

> How is the reusable workflow performed?

The adapter should answer:

> How do we talk to an external system?

Keeping those questions separate made the project much easier to understand after taking a break.

## Next

After routing, the next major backend concept is authentication: registration, login, JWT tokens, protected routes, and role-based access.
