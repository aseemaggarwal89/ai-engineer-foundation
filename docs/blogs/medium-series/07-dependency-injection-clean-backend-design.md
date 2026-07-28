# 07 - Dependency Injection in FastAPI: The Backbone of Clean Backend Design

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)

Dependency injection was one of those concepts that looked simple at first, but became more important as the project grew.

In the beginning, I thought it only meant:

```text
Use Depends(...) in FastAPI.
```

But while building this backend, I realized something better:

> Dependency injection is not just a FastAPI feature. It is a design habit.

It helps the code answer one question clearly:

```text
Who creates the object, and who uses the object?
```

That question matters a lot in a backend that has routes, use cases, repositories, authentication, Redis, Ollama, OpenAI, model routing, and response pipelines.

## The Problem Without Dependency Injection

Imagine writing a route like this:

```python
async def register_user(request):
    session = AsyncSessionLocal()
    repo = SQLAlchemyUserRepository(session)
    use_case = RegisterUserUseCase(repo)
    return await use_case.execute(...)
```

This works for a small demo.

But it creates problems quickly:

- the route knows too much
- testing becomes harder
- database details leak into HTTP code
- replacing implementations becomes painful
- resource cleanup becomes unclear

The route should not build the whole world.

The route should receive the application operation it needs.

## The Simple Idea

Dependency injection means:

```text
A class or function receives what it needs from outside.
```

For example, the registration use case receives a repository:

```python
class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
```

The use case does not create SQLAlchemy.

It does not know FastAPI exists.

It only knows:

```text
I need something that behaves like a UserRepository.
```

That is clean design.

## FastAPI `Depends` Is The Wiring Mechanism

FastAPI then wires the use case at the HTTP boundary:

```python
def get_register_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repo)
```

So there are two ideas working together:

```text
Constructor injection
-> application classes receive dependencies explicitly

FastAPI Depends
-> FastAPI resolves those dependencies for a request
```

This was the big learning for me.

Dependency injection is the principle.

`Depends(...)` is one tool FastAPI gives us to apply it.

## Where Dependencies Live In This Project

The project keeps FastAPI dependency providers under:

```text
app/dependencies/
```

The main files are:

```text
app/dependencies/deps.py
app/dependencies/repositories.py
app/dependencies/use_cases.py
app/dependencies/ai_dependencies.py
```

Security dependencies live under:

```text
app/security/
```

The AI container lives in:

```text
app/application/ai/core/container.py
```

This separation gives the project a clear rule:

```text
Routes call use cases.
Dependency providers build use cases.
Use cases receive interfaces or services.
Infrastructure is selected in the wiring layer.
```

## Database Session Wiring

The database session dependency lives in:

```text
app/dependencies/deps.py
```

It looks like this:

```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

The `yield` is important.

It means:

```text
before yield
-> create the session

during yield
-> route, use case, and repository can use the session

after request
-> async context manager closes the session
```

This makes the database session request-scoped.

That is important because a SQLAlchemy `AsyncSession` represents request or unit-of-work state. It should not be stored in a global container and shared across requests.

## Repository Wiring

The repository provider lives in:

```text
app/dependencies/repositories.py
```

The user repository is wired like this:

```python
def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
    settings=Depends(settings),
) -> UserRepository:
    return SQLAlchemyUserRepository(session, settings)
```

This gives a clean chain:

```text
route
-> use case
-> UserRepository interface
-> SQLAlchemyUserRepository implementation
-> request-scoped AsyncSession
```

The route does not know SQLAlchemy.

The use case does not know how the database session is created.

The dependency layer connects them.

## Use Case Wiring

Use-case providers live in:

```text
app/dependencies/use_cases.py
```

Example:

```python
def get_login_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
) -> LoginUserUseCase:
    return LoginUserUseCase(user_repo)
```

These providers are normal `def`, not `async def`.

That is intentional.

They are only creating lightweight Python objects.

Use `async def` for a dependency only when it needs to await I/O or manage an async resource.

This is a small readability rule, but it keeps the project easier to reason about.

## Authentication Dependency Flow

Protected routes use dependencies from:

```text
app/security/security.py
app/security/dependencies.py
app/security/authorization.py
```

The flow looks like this:

```text
protected route
-> get_current_active_user
-> get_current_user
-> get_token_payload
-> decode JWT
-> load user from database
```

Admin routes add:

```python
Depends(require_role(UserRole.ADMIN))
```

This means authorization is also dependency-driven.

The route does not manually decode tokens or manually query the user table.

It asks FastAPI for the current user or required role.

## AI Dependency Wiring

The AI route is:

```text
POST /ai/summarize
```

The route depends on:

```python
use_case: SummarizeTextUseCase = Depends(get_summarize_use_case)
```

The AI dependency graph is:

```text
route
-> get_summarize_use_case
-> get_summary_service
-> get_container
-> request.app.state.container
```

The container is created once during application startup:

```python
container = ServiceContainer(settings)
await container.startup()
app.state.container = container
```

It owns reusable AI infrastructure:

- Ollama HTTP client
- OpenAI client when configured
- Redis client
- model registry
- inference router
- provider adapters
- pipeline registry
- guardrails and validators

This avoids creating expensive network clients on every request.

## Container Without Service Locator

This part is important.

The dependency layer can access:

```text
request.app.state.container
```

But the use case should not receive the whole container.

This would be a bad pattern:

```python
class SummarizeTextUseCase:
    def __init__(self, container):
        self.container = container
```

Why?

Because the real dependencies become hidden.

Instead, the project does this:

```text
dependency provider reads container
-> extracts guardrails, safety filter, service, settings
-> passes them explicitly into the use case
```

So the use case still has clear constructor dependencies.

That keeps the container as composition infrastructure, not a service locator.

## Dependency Scope

Another important learning was dependency lifetime.

Some objects should be created once and reused.

Some should be created per request.

Some are cheap and can be created whenever needed.

In this project:

```text
Application-scoped
-> settings
-> ServiceContainer
-> Ollama client
-> OpenAI client
-> Redis client
-> model registry
-> inference router
```

```text
Request-scoped
-> database session
-> current user
-> request body
-> request ID context
```

```text
Lightweight/transient
-> use cases
-> repositories
-> SummaryService
```

The key rule is:

> Shared application-scoped objects must be stateless or safe for concurrent use.

Request-specific mutable state should stay request-scoped.

That is why the app shares an HTTP client, but does not share one database session across all requests.

## FastAPI Caches Dependencies Per Request

FastAPI normally caches the same dependency result within one request.

That means if two dependencies need the same `get_db_session`, FastAPI can reuse that result during the request.

But this is request-level caching.

It does not mean the object becomes global.

On the next request, request-scoped dependencies are resolved again.

This is one of those FastAPI details that makes dependency wiring both powerful and easy to misunderstand.

## Testing Becomes Easier

This is where dependency injection becomes very practical.

In route tests, I can replace the real AI use case:

```python
def override_summarize_use_case():
    return fake_use_case

app.dependency_overrides[get_summarize_use_case] = (
    override_summarize_use_case
)
```

Now the test can call:

```text
POST /ai/summarize
```

without calling Ollama, OpenAI, or Redis.

After the test, overrides should be cleared:

```python
app.dependency_overrides.clear()
```

This prevents one test from accidentally affecting another.

The testing idea is simple:

```text
route test
-> replace use case

use-case test
-> replace repository

service test
-> replace cache or provider port
```

Each test replaces the dependency at the right boundary.

## Why This Helps AI Backends

AI integration has many things that may change:

- local model provider
- cloud model provider
- cache implementation
- prompt strategy
- response validation
- fallback policy
- observability
- future RAG components

Dependency injection gives those pieces a place to connect without spreading construction logic everywhere.

For example, the route should not care whether summarization uses:

```text
Ollama
OpenAI
cache hit
cache miss
fallback provider
response pipeline
```

The route only calls:

```python
await use_case.execute(request.text)
```

That is the kind of simplicity dependency injection makes possible.

## What I Learned

Dependency injection helped me understand why clean backend code feels easier to revisit after a break.

The route is not overloaded.

The use case is explicit.

The repository receives its session.

The AI service receives its ports.

The container owns reusable infrastructure.

The test can replace the right boundary.

My final mental model is:

```text
Routes should ask for actions.
Use cases should ask for collaborators.
Dependency providers should wire objects.
Infrastructure should be created in one clear place.
```

That is the backbone of clean backend design.

## Next

After dependency injection, the next phase is AI integration architecture: provider adapters, model routing, local Ollama support, cloud OpenAI support, caching, guardrails, and response validation.
