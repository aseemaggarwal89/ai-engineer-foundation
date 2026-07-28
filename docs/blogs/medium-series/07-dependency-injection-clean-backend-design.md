# 07 - Dependency Injection in FastAPI: The Backbone of Clean Backend Design

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


Dependency injection is one of the most important concepts I learned while building this project.

At first, dependency injection looked like a FastAPI feature for passing objects into routes.

Later, I realized it is much more important.

Dependency injection is what keeps the project clean, testable, and maintainable.

## What Is Dependency Injection?

Dependency injection means:

> A function or class receives what it needs instead of creating everything itself.

Instead of this:

```python
def route():
    repo = SQLAlchemyUserRepository()
    use_case = RegisterUserUseCase(repo)
```

We do this:

```python
def route(use_case: RegisterUserUseCase = Depends(get_register_user_use_case)):
    ...
```

FastAPI resolves the dependency.

## Why This Matters

Dependency injection helps with:

- separation of concerns
- testing
- replacing implementations
- clean architecture
- avoiding hardcoded dependencies

This matters even more for AI integration, because AI systems have many moving parts:

- provider clients
- caches
- model routers
- validators
- prompt builders
- pipelines
- registries

## Dependency Files

The project organizes dependencies in:

```text
app/dependencies/
```

Important files:

```text
deps.py
repositories.py
use_cases.py
ai_dependencies.py
```

Each file wires a different part of the system.

## Database Session Dependency

The database session is provided as a dependency:

```python
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
```

Repositories receive this session.

Routes do not create database sessions directly.

## Repository Dependency

A repository dependency creates the concrete repository:

```python
def get_user_repository(session: AsyncSession = Depends(get_db_session)):
    return SQLAlchemyUserRepository(session, settings)
```

The use case depends on the repository interface.

The route does not know SQLAlchemy.

## Use Case Dependency

A use case dependency wires business workflow:

```python
def get_register_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repo)
```

This keeps construction in one place.

## AI Dependency Wiring

AI dependency wiring lives in:

```text
app/dependencies/ai_dependencies.py
```

It connects FastAPI requests to the AI container:

```text
request.app.state.container
-> SummaryService
-> SummarizeTextUseCase
```

The container owns long-lived resources:

- Ollama HTTP client
- OpenAI client
- Redis client
- model registry
- pipeline registry
- guardrails
- provider adapters

The request dependency builds lightweight service/use case objects from those reusable components.

## Why Not Create Clients Per Request?

AI providers and Redis use network connections.

Creating clients per request would be inefficient.

So the project creates them once during app startup:

```python
container = ServiceContainer(settings)
app.state.container = container
```

Then dependencies reuse them.

## Testing Benefit

Dependency injection makes testing easier.

In tests, you can override dependencies:

```python
app.dependency_overrides[get_summarize_use_case] = fake_use_case
```

This lets you test routes without calling real AI providers.

## Enterprise Lesson

In enterprise applications, dependency injection is not optional architecture decoration.

It is what allows:

- clean boundaries
- easier testing
- provider replacement
- controlled resource lifecycle
- environment-specific configuration

## What I Learned

Dependency injection helped me understand how FastAPI can support clean architecture.

The route does not build the world.

It asks for the use case.

The dependency layer wires everything behind the scenes.

## Next

After backend foundations, the next phase is AI integration architecture.
