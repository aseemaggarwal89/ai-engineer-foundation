# Setting Up a FastAPI Backend Project the Right Way

The first phase of this project was learning how to structure a FastAPI backend.

A simple FastAPI project can start with one `main.py` file.

That is fine for learning routes.

But once the project grows, one file quickly becomes difficult to maintain.

So I structured the project into layers.

## Why Project Structure Matters

Backend code becomes easier to understand when every folder has a clear responsibility.

In this project:

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
  application/ai/
```

This makes the code easier to navigate after a break.

## The Role of main.py

The application entry point is:

```text
app/main.py
```

This file is responsible for:

- creating the FastAPI app
- configuring logging
- configuring tracing
- adding middleware
- registering routers
- registering exception handlers
- starting long-lived resources during lifespan startup

It should not contain business logic.

## FastAPI Lifespan

The app uses FastAPI lifespan to create resources once per process.

During startup, the project creates:

```python
container = ServiceContainer(settings)
await container.startup()
app.state.container = container
```

This is important for AI integration because provider clients, Redis clients, and registries should not be recreated for every request.

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

This keeps API endpoints grouped by feature.

## Dependencies Folder

Dependency wiring lives under:

```text
app/dependencies/
```

This folder connects FastAPI dependency injection with application objects.

For example:

```text
get_summarize_use_case
get_summary_service
get_user_repository
get_db_session
```

This keeps object construction outside route handlers.

## Domain Layer

The domain layer contains business concepts:

```text
app/domain/
  entities/
  interfaces/
  use_cases/
  exceptions/
```

This layer should not depend on FastAPI.

That makes business logic easier to test and reason about.

## Repository Layer

Repositories live in:

```text
app/repositories/
```

They implement database operations using SQLAlchemy.

The domain defines repository interfaces, and infrastructure implements them.

This separation helps keep business logic independent from database details.

## Core Layer

The core layer contains cross-cutting concerns:

```text
app/core/
  config.py
  logging.py
  metrics.py
  tracing.py
  retry.py
  timeout.py
  exception_handlers.py
  middleware/
```

These are not specific to one feature.

They support the whole application.

## AI Application Layer

The AI layer lives under:

```text
app/application/ai/
```

It contains:

- AI use cases
- AI services
- provider adapters
- model routing
- prompts
- guardrails
- response pipelines
- cache abstraction

This keeps AI-specific logic separate from auth, users, health checks, and database concerns.

## Clean Architecture Idea

The project follows a simple clean architecture direction:

```text
Route
-> Use Case
-> Service
-> Interface
-> Infrastructure
```

The inner application logic should not depend directly on external tools.

For example:

- route does not know Ollama
- use case does not know Redis
- service depends on inference and cache ports
- adapters know provider-specific APIs

## What I Learned

The main lesson from project setup was:

> Folder structure is not decoration. It is a memory tool and a maintenance tool.

When the code is layered clearly, I can return after a break and quickly understand where to start.

## Next

After setting up the backend structure, the next step was database migration with Alembic.

