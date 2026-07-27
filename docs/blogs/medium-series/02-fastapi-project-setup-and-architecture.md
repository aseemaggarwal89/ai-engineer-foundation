# Setting Up a FastAPI Backend Project the Right Way

When I started this project, my first goal was simple:

```text
Learn Python FastAPI by building a real backend service.
```

But very quickly I realized something important.

A backend project is not only about creating endpoints.

It also needs:

- clear folder structure
- configuration management
- database setup
- routing conventions
- dependency wiring
- error handling
- middleware
- testability
- future extensibility

This became even more important because the long-term goal of the project was AI integration.

If the base backend structure is messy, the AI implementation also becomes messy.

So before adding Ollama, OpenAI, Redis caching, guardrails, and model routing, I focused on creating a maintainable FastAPI foundation.

Project repository:

[AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)

## Why Project Structure Matters

A small FastAPI app can start with one file:

```text
main.py
```

That is fine for a quick demo.

But for a learning project that is trying to become production-style, one file becomes difficult to understand.

After a break, I do not want to ask:

```text
Where is authentication?
Where is database logic?
Where is AI provider logic?
Where are request schemas?
Where are errors handled?
Where is dependency injection configured?
```

The folder structure should answer those questions.

That is why this project is organized into layers.

## High-Level Project Structure

The application is organized like this:

```text
app/
  main.py
  routers/
  dependencies/
  domain/
  repositories/
  db/
  schemas/
  security/
  services/
  core/
  application/
    ai/
```

Each folder has a responsibility.

The goal is not to make the project look complex.

The goal is to make the project easier to navigate as features grow.

## The Role Of `main.py`

The application entry point is:

```text
app/main.py
```

This file creates and configures the FastAPI application.

Its job is application assembly, not business logic.

In this project, `main.py` is responsible for:

- creating the FastAPI app
- configuring logging
- configuring tracing
- registering middleware
- registering routers
- registering exception handlers
- starting long-lived resources during lifespan startup
- shutting down clients cleanly

The important idea is:

```text
main.py should wire the application together.
It should not contain the actual business workflow.
```

That keeps the entry point readable.

## Application Startup With Lifespan

FastAPI provides a lifespan hook for startup and shutdown logic.

This project uses lifespan to create long-lived resources once per process.

Example:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    container = ServiceContainer(settings)
    await container.startup()
    app.state.container = container

    yield

    await container.shutdown()
```

This matters because AI backends often use reusable infrastructure:

- HTTP clients
- OpenAI client
- Ollama client
- Redis client
- model registry
- inference router
- response pipelines

These objects should not be recreated for every request.

The lifespan hook gives the backend a clean startup and shutdown lifecycle.

## Request Flow At The Application Level

Before any route handler runs, the request passes through application-level concerns.

The simplified flow looks like this:

```text
HTTP request
-> middleware
-> router
-> dependency injection
-> use case
-> service
-> infrastructure
-> response
```

This shape is useful because every layer has a different job.

For example:

- middleware handles request IDs, metrics, limits
- routers handle HTTP inputs and outputs
- use cases coordinate business actions
- services implement workflow logic
- infrastructure talks to external systems

This separation becomes very important when adding AI.

## Routers Folder

Routes live under:

```text
app/routers/routes/
```

Examples:

```text
ai.py
auth.py
admin.py
health.py
metrics.py
```

Each file groups endpoints by feature.

For example:

- `auth.py` handles register and login APIs
- `health.py` handles health checks
- `metrics.py` exposes Prometheus metrics
- `ai.py` exposes AI APIs such as summarization

This keeps route files small and focused.

## Router Responsibility

A route should not know too much.

For example, the AI route should not directly know:

- how Ollama works
- how OpenAI works
- how Redis caching works
- how fallback works
- how model output is validated

The route should receive an HTTP request, call a use case, and return an HTTP response.

That is why route handlers use dependency injection.

## Dependencies Folder

Dependency wiring lives under:

```text
app/dependencies/
```

This folder connects FastAPI dependency injection with application objects.

Examples:

```text
get_summarize_use_case
get_summary_service
get_user_repository
get_db_session
```

This keeps construction logic outside route handlers.

Instead of building everything manually inside each endpoint, the route asks FastAPI for the object it needs.

That makes the code cleaner and easier to test.

## Domain Layer

The domain layer contains business concepts.

In this project, it includes:

```text
app/domain/
  entities/
  interfaces/
  use_cases/
  exceptions/
```

This layer should not depend on FastAPI.

That is important because business rules should not be locked inside the web framework.

For example:

- user-related use cases should not know HTTP details
- domain exceptions should not directly depend on route logic
- repository interfaces should describe what the application needs, not how SQLAlchemy works

This makes the core logic easier to reason about.

## Repository Layer

Repositories live in:

```text
app/repositories/
```

They implement database operations.

The domain layer can define repository interfaces, and the repository layer can implement those interfaces using SQLAlchemy.

This avoids spreading database logic across routes and services.

Instead of writing database queries in route handlers, the application uses repository objects.

That makes future changes easier.

For example, if the database implementation changes, the route should not need to change.

## Database Layer

Database setup lives under:

```text
app/db/
```

This includes:

- database engine
- SQLAlchemy base
- ORM models
- session handling

The project also uses Alembic migrations, which I will cover in the next post.

For now, the important lesson is:

```text
Database models and database sessions should be isolated from route handlers.
```

This keeps the HTTP layer clean.

## Schemas Layer

Schemas live under:

```text
app/schemas/
```

Schemas define request and response shapes.

FastAPI works very well with Pydantic models.

For example, APIs can declare:

```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

This gives:

- request validation
- generated OpenAPI docs
- better editor support
- clearer API contracts

For AI APIs, schemas are especially useful because model input and output need to be controlled.

## Security Layer

Security-related code lives under:

```text
app/security/
```

This includes:

- password hashing
- JWT creation
- token decoding
- current user resolution

Authentication should not be mixed with every route.

Routes should depend on reusable security utilities and use cases.

This keeps login, protected routes, and role checks consistent.

## Core Layer

The core layer contains cross-cutting application concerns:

```text
app/core/
  config.py
  logging.py
  metrics.py
  tracing.py
  exception_handlers.py
  middleware/
```

These features support the whole application.

They are not specific to users, auth, health, or AI.

Examples:

- `config.py` loads environment-based settings
- `logging.py` configures structured logs
- `metrics.py` defines Prometheus metrics
- `tracing.py` configures OpenTelemetry
- `exception_handlers.py` maps domain errors to HTTP responses
- `middleware/` contains request ID, metrics, and body-size middleware

This separation helps avoid duplicate code.

## AI Application Layer

The AI layer lives under:

```text
app/application/ai/
```

This is where the AI-specific architecture is placed.

It includes:

- AI use cases
- AI services
- provider adapters
- inference router
- model registry
- prompts
- guardrails
- response validation
- response pipelines
- Redis cache abstraction

This is one of the most important decisions in the project.

AI code is not placed randomly inside routes.

It has its own application boundary.

That makes the backend easier to extend with future capabilities such as:

- chat
- summarization
- document Q&A
- RAG
- embeddings
- agents

## Clean Architecture Direction

The project follows a simple clean architecture direction:

```text
Route
-> Use Case
-> Service
-> Port / Interface
-> Infrastructure Adapter
```

Example AI flow:

```text
POST /ai/summarize
-> SummarizeTextUseCase
-> SummaryService
-> AIInferencePort
-> InferenceRouter
-> OllamaAdapter or OpenAIAdapter
```

This means the route does not directly call the model provider.

The service depends on a port.

The infrastructure adapter implements that port.

This makes the code easier to change.

## Why This Helps AI Integration

Without structure, AI integration often becomes:

```text
route -> prompt -> model API -> return response
```

That works for a demo.

But it becomes hard to maintain when we add:

- multiple providers
- provider fallback
- Redis caching
- request guardrails
- response validation
- logging
- tracing
- cost control
- future RAG

The architecture gives every concern a place.

That is the real benefit.

## Scalability And Readability Lessons

For me, scalability is not only about handling more traffic.

It is also about handling more code.

A readable backend makes it easier to:

- add new features
- debug problems
- onboard another developer
- test business logic
- replace infrastructure
- explain the project in interviews

The project structure becomes a map.

When I return after a break, I can follow the folders and understand the system again.

## What I Learned

The biggest lesson from setting up the FastAPI project was:

```text
Good architecture is a memory tool.
```

It helps the future version of me understand why the code was written in a certain way.

Before this project, I thought AI integration started with calling a model API.

Now I understand that AI integration starts earlier.

It starts with a backend foundation that can support the AI workflow cleanly.

## Next

In the next post, I will explain how I added database migrations using Alembic.

That step made the project feel more like a real backend system because the database schema became version-controlled instead of manually managed.
