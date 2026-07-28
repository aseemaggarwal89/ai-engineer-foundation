# 13 - Testing, Debugging, and Public Repo Readiness for a FastAPI AI Backend

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


After implementing the AI backend, I wanted to make the project public and use it for learning, interviews, and blog posts.

That created a new question:

```text
How do I prove that the project works and is safe to share?
```

This post covers the testing and debugging mindset around the project.

## Why Testing AI Backends Is Different

Traditional backend tests often check:

- status code
- JSON response
- database writes
- authentication behavior

AI backends also need to check:

- prompt validation
- provider fallback behavior
- response validation
- cache behavior
- refusal detection
- timeout handling
- safe error handling

The model output may not be deterministic, so the code around the model must be designed to be testable.

## Test The Workflow Around The Model

The most important lesson is:

```text
Do not make every test depend on a real model call.
```

Real model calls are:

- slow
- expensive
- sometimes unavailable
- non-deterministic

So tests should focus on the deterministic parts of the system.

Examples:

- routes call the correct use case
- guardrails reject invalid input
- pipelines reject invalid model output
- cache keys are stable
- provider adapters normalize errors
- fallback runs when primary provider fails

## FastAPI Dependency Overrides

FastAPI provides `dependency_overrides`, which is very useful for testing.

In the health endpoint tests, the project replaces real use cases with fake ones.

Example pattern:

```python
app = create_app()
app.dependency_overrides[get_liveness_usecase] = lambda: FakeLivenessUseCase()
client = TestClient(app)

response = client.get("/health/live")
```

This makes route tests fast and focused.

The route test does not need a real database or model provider.

It only checks HTTP behavior.

## Testing AI Pipelines

The project has tests for `ChatPipeline`.

The pipeline checks:

- normal response cleanup
- empty response rejection
- common refusal response rejection

Example:

```python
with pytest.raises(ResponseValidationError):
    pipeline.run("   \n  ")
```

This is valuable because response validation should be deterministic.

The test does not need OpenAI or Ollama.

It tests the rule:

```text
Never return empty model output as a successful answer.
```

## What To Add Next In Tests

Useful next tests for this project:

- summarization pipeline parses bullets correctly
- unsafe prompt is rejected before provider call
- cache hit avoids inference call
- cache miss calls inference and stores response
- primary provider failure triggers fallback
- missing fallback returns safe error
- request body limit blocks oversized input
- OpenAI configuration fails fast when key is missing

These tests would make the AI workflow easier to explain in interviews.

## Debugging From Logs

The project uses structured logs with request IDs.

That means one request can be followed through the system.

Example AI logs may show:

```text
ai_inference_completed
ai_inference_response_received
Failed to export traces to otel-collector:4317
```

This tells me:

```text
The AI request completed.
The model returned a response.
Tracing export failed separately.
```

So the model integration is working.

The issue is observability infrastructure.

This distinction is important when debugging production systems.

## Debugging Checklist

When an AI request fails, I can walk through the lifecycle:

```text
1. Did the request reach FastAPI?
2. Did middleware reject it?
3. Did authentication pass?
4. Did request validation pass?
5. Did guardrails accept the prompt?
6. Was there a cache hit?
7. Which provider was selected?
8. Did primary provider fail?
9. Did fallback run?
10. Did response validation pass?
11. Was the response cached?
12. Was the final HTTP response safe?
```

This checklist turns a confusing AI failure into a step-by-step investigation.

## Postman And Swagger Testing

For manual testing, useful endpoints include:

```http
GET /health/live
GET /health/ready
GET /health/deep
GET /metrics
POST /auth/register
POST /auth/login
POST /ai/summarize
```

For `POST /ai/summarize`, the request body can be:

```json
{
  "text": "FastAPI is a modern Python web framework. It supports async routes, dependency injection, validation, and automatic OpenAPI documentation.",
  "max_bullets": 3
}
```

This is a good demo request because it exercises:

- routing
- schema validation
- dependency injection
- guardrails
- provider routing
- response pipeline
- JSON response

## Public Repo Readiness

Before sharing the repository publicly, I should verify:

- `.env` is not committed
- API keys are not committed
- old keys are rotated if they were ever exposed
- sample env values are documented separately
- logs and screenshots do not show secrets
- README explains how to run locally
- Docker Compose services are documented
- tests can be run by another developer
- blog posts link to docs instead of private local paths

This matters because public repositories are indexed quickly.

Secrets should be treated as exposed if they were ever pushed publicly.

## README Checklist

A public learning project should help someone else run it.

The README should explain:

- project purpose
- architecture overview
- local setup
- required environment variables
- Docker Compose startup
- database migration commands
- how to run tests
- sample API requests
- AI provider configuration
- troubleshooting notes

This turns the repo from a code dump into a learning resource.

## Interview Value

This project can help in AI backend interviews because it shows:

- backend fundamentals
- async Python understanding
- API design
- dependency injection
- clean architecture
- model provider abstraction
- guardrails
- caching
- observability
- production thinking
- debugging maturity

Even if tools like LiteLLM provide similar provider-routing features, implementing the workflow yourself builds the mental model.

That mental model is what interviewers usually test.

## What I Learned

Making a project public is not only about pushing code.

It is about making the project understandable, runnable, and explainable.

The best portfolio projects show both implementation and learning.

## Next

The next technical milestone is covered in the RAG roadmap: embeddings, vector search, grounded prompts, and source-aware answers.
