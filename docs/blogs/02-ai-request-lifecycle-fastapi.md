# 02 - The AI Request Lifecycle: From Postman to Model Response

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


When you send a request to an AI API, it can look simple from the outside.

In Postman, the request is just:

```http
POST http://127.0.0.1:8000/ai/summarize
Content-Type: application/json
```

Body:

```json
{
  "text": "FastAPI is a modern Python web framework..."
}
```

But inside the backend, the request moves through many layers before it becomes a model response.

This article explains that lifecycle using the `AI Engineer Foundation` project.

## Step 1: The FastAPI Route Receives the Request

The AI route is defined in:

```text
app/routers/routes/ai.py
```

The route accepts a `SummaryRequest`:

```python
class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=1)
```

Pydantic validates the request body before the use case runs.

If `text` is missing or empty, FastAPI returns a validation error before the AI workflow begins.

## Step 2: Dependency Injection Builds the Use Case

FastAPI injects the summarization use case from:

```text
app/dependencies/ai_dependencies.py
```

The dependency function creates:

- `SummaryService`
- `SummarizeTextUseCase`
- AI guardrails
- safety filter
- cache
- inference router

This is useful because the route does not create concrete services directly.

The route depends on behavior, not construction details.

## Step 3: The Use Case Applies Request-Side Safety

The use case lives in:

```text
app/application/ai/usecases/summarize_text.py
```

The workflow starts with safety checks:

```python
self.safety.check(text)
text = self.guardrails.validate_prompt(text)
```

The safety filter blocks sensitive terms such as:

- `credit card`
- `cvv`
- `password`
- `ssn`

The guardrails handle:

- empty input
- prompt size limits
- binary/control character detection
- whitespace normalization
- soft truncation for long prompts

This protects both the application and the model provider.

## Step 4: The Summary Service Builds the Prompt

After input validation, the use case delegates to:

```text
app/application/ai/services/summary_service.py
```

The service builds a final LLM prompt using:

```text
app/application/ai/prompts/summary_prompt.py
```

Prompt construction is kept separate so you can version and test prompts independently.

## Step 5: The Service Checks Redis Cache

AI calls can be slow and expensive.

Before calling the model, the service builds a cache key using:

- capability
- prompt
- model
- temperature
- max tokens

The cache implementation is:

```text
app/application/ai/infrastructure/redis_ai_cache.py
```

If Redis has a cached answer, the service returns it immediately.

If not, the workflow continues to inference.

## Step 6: The Inference Router Selects a Provider

The service calls:

```python
await self.inference.generate(...)
```

The concrete inference implementation is:

```text
app/application/ai/infrastructure/ai_inference_port.py
```

Despite the filename, this class is the `InferenceRouter`.

Its job is to:

1. ask the model registry for the primary provider
2. try the primary provider
3. if the provider fails, try the fallback provider
4. return raw model text

The route does not know whether the provider is Ollama or OpenAI.

## Step 7: The Provider Adapter Calls the Model

For local AI, the project uses:

```text
app/application/ai/infrastructure/ollama_adapter.py
```

It sends a request to:

```text
POST /api/generate
```

For cloud AI, the project uses:

```text
app/application/ai/infrastructure/openai_adapter.py
```

Both adapters implement `AIModelPort`, so the rest of the application sees the same interface.

## Step 8: The Response Pipeline Validates Model Output

The raw model response is not returned directly.

It goes through:

```text
app/application/ai/core/summarization_pipeline.py
```

The pipeline does this:

```text
raw response
-> validate raw text
-> parse bullets
-> validate bullets
-> hallucination guard
-> score quality
```

Only validated structured bullets are returned to the API client.

## Step 9: The Validated Response Is Cached

The service caches only the final trusted output:

```python
await self.cache.set(cache_key, json.dumps(bullets), ttl=3600)
```

This is an important design choice.

You do not want to cache broken, raw, or unvalidated model output.

## Step 10: The API Returns the Response

Finally, the route returns:

```python
return SummaryResponse(bullets=bullets)
```

The client receives:

```json
{
  "bullets": [
    "FastAPI is used to build APIs.",
    "The backend validates prompts before calling AI.",
    "The service caches validated AI responses."
  ]
}
```

## Full Lifecycle Summary

```text
Postman
-> FastAPI route
-> Pydantic request schema
-> dependency injection
-> use case
-> safety filter
-> guardrails
-> prompt builder
-> Redis cache
-> inference router
-> model registry
-> Ollama/OpenAI adapter
-> response pipeline
-> cache write
-> API response
```

## Final Thought

A production-style AI endpoint is not only a model call.

It is a complete request lifecycle with validation, routing, fallback, caching, observability, and response safety.
