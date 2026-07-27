# Creating a Clean Routing Mechanism in FastAPI

Routing is where HTTP requests enter the application.

In a small project, all routes can live in `main.py`.

In a real project, routes should be organized by feature.

This project uses separate route modules for:

- auth
- admin
- health
- metrics
- AI

## Router Folder Structure

Routes live under:

```text
app/routers/routes/
```

Examples:

```text
auth.py
admin.py
health.py
metrics.py
ai.py
```

Central router registration happens in:

```text
app/routers/routers.py
```

This file includes all routers into the FastAPI app.

## Why Separate Routes?

Separate route files help with:

- readability
- feature ownership
- testing
- security boundaries
- future scaling

For example, auth routes and AI routes have very different responsibilities.

Keeping them separate makes the project easier to understand.

## Public and Protected Routes

The project separates public and protected route behavior.

Examples of public routes:

```text
POST /auth/register
POST /auth/login
GET /health/live
POST /ai/summarize
```

Examples of protected routes:

```text
GET /auth/me
GET /auth/users
GET /admin/dashboard
```

Protected routes use FastAPI dependencies to verify the current user or role.

## AI Route Example

The AI route lives in:

```text
app/routers/routes/ai.py
```

Its job is intentionally small:

```python
bullets = await use_case.execute(request.text)
return SummaryResponse(bullets=bullets)
```

The route does not contain:

- provider logic
- Redis logic
- fallback logic
- prompt validation
- response parsing

That logic belongs in the AI application layer.

## Route Tags and Prefixes

FastAPI routers use prefixes and tags:

```python
public_router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)
```

This gives clean endpoint grouping:

```text
/ai/summarize
```

It also organizes Swagger UI documentation.

## Dependency Injection At Route Level

Routes receive use cases through dependencies:

```python
use_case: SummarizeTextUseCase = Depends(get_summarize_use_case)
```

This is one of FastAPI's strongest features.

The route asks for a use case, and FastAPI builds it using dependency functions.

## Why Routes Should Stay Thin

Thin routes are easier to:

- test
- read
- secure
- document
- change

If a route becomes too large, it usually means business logic is leaking into the HTTP layer.

## Enterprise Lesson

In enterprise applications, routing is not only about URL mapping.

It is also about:

- request boundaries
- security boundaries
- versioning
- feature grouping
- dependency injection
- API documentation

## What I Learned

The route should answer:

> What HTTP endpoint is this?

The use case should answer:

> What application action happens?

The service should answer:

> How is the workflow orchestrated?

Keeping those questions separate made the project much easier to understand.

## Next

After routing, the next major backend concept is authentication.

