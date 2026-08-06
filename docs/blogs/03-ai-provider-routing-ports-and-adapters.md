# 03 - Using Ports and Adapters for Ollama and OpenAI Provider Routing

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


One of the most useful design decisions in this project is that the application does not directly depend on Ollama or OpenAI.

Instead, it uses ports and adapters.

That means the application defines what it needs, and infrastructure classes decide how to provide it.

## The Problem

Imagine your service directly calls Ollama from the business logic:

```python
response = await httpx.post("http://ollama:11434/api/generate", json=payload)
```

That works, but it creates problems:

- switching to OpenAI requires changing business logic
- fallback becomes messy
- tests need real provider behavior or complicated mocking
- every service needs to understand provider-specific APIs

The better approach is to hide provider details behind an interface.

## The AI Model Port

The provider contract lives in:

```text
app/application/ai/domain/ai_model_port.py
```

It defines one behavior:

```python
class AIModelPort(ABC):
    async def generate(
        self,
        *,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        ...
```

This is the port.

The application says:

> I need something that can generate text from a prompt.

It does not say:

> I need Ollama or OpenAI.

## Provider Adapters

The project has two provider adapters:

```text
app/application/ai/infrastructure/ollama_adapter.py
app/application/ai/infrastructure/openai_adapter.py
```

Both implement `AIModelPort`.

That gives the application one common way to call different providers.

## Ollama Adapter

The Ollama adapter translates the common contract into Ollama's local HTTP API.

It creates a payload like:

```python
payload = {
    "model": model,
    "prompt": prompt,
    "options": {
        "temperature": temperature,
        "num_predict": max_tokens,
    },
    "stream": False,
}
```

Then it calls:

```text
POST /api/generate
```

The generated text is read from:

```python
data.get("response")
```

## OpenAI Adapter

The OpenAI adapter translates the same application contract into OpenAI's API shape.

It calls:

```python
response = await self.client.responses.create(
    model=model,
    input=prompt,
    temperature=temperature,
    max_output_tokens=max_tokens,
)
```

Then it extracts:

```python
response.output_text
```

## Normalizing Provider Errors

Every provider has its own error types.

OpenAI can raise:

- rate limit errors
- API errors
- timeout errors

Ollama uses HTTP and transport errors through `httpx`.

The application should not care about those details.

So both adapters normalize provider failures into:

```python
AIProviderError
```

That lets the router handle fallback consistently.

## Model Registry

Provider routing is controlled by:

```text
app/core/model_registry.py
```

The registry maps AI capabilities to providers.

For example:

```env
AI__MODEL_REGISTRY__SUMMARIZATION__PRIMARY=ollama
AI__MODEL_REGISTRY__SUMMARIZATION__FALLBACK=openai
```

This means:

- use Ollama first for summarization
- if Ollama fails, try OpenAI

## Inference Router

The inference router lives in:

```text
app/application/ai/infrastructure/inference_router.py
```

Its workflow is:

```text
get primary provider
-> try primary
-> if primary raises AIProviderError
-> get fallback provider
-> try fallback
-> return raw text
```

This is the key design:

```python
primary = self.registry.get_primary(capability)
fallback = self.registry.get_fallback(capability)
```

The caller asks for a capability, not a vendor.

## Why This Follows SOLID

This design supports several SOLID principles.

### Single Responsibility

Each class has one job:

- adapter talks to one provider
- registry maps capability to provider
- router handles fallback
- service owns application workflow

### Open/Closed

You can add a new provider by creating a new adapter and registering it.

Existing use cases do not need to change.

### Dependency Inversion

Application services depend on interfaces such as `AIInferencePort` and `AIModelPort`, not low-level HTTP clients.

## Why This Matters

AI providers change.

Models change.

Prices change.

Local development and production may use different providers.

With ports and adapters, you can evolve the infrastructure without rewriting the application workflow.

## Final Thought

Provider routing is not just a nice abstraction.

It is what lets an AI backend remain flexible as the AI ecosystem changes.
