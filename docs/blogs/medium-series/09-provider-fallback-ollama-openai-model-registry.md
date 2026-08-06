# 09 - Provider Abstraction: Ollama, OpenAI, Model Registry, and Inference Router

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)

In the previous blog, I explained the full AI request pipeline.

Now I want to zoom into one specific part of that pipeline:

```text
provider abstraction
-> model registry
-> inference router
-> fallback
-> resilience
```

This is the part of the backend that answers a deceptively simple question:

> Which AI provider should actually execute this request?

When I started, I thought AI integration meant writing code like this:

```text
if using local model:
    call Ollama
else:
    call OpenAI
```

That works for a small experiment.

But it does not scale well as a backend design.

If application logic directly calls Ollama, then switching to OpenAI becomes a code change.

If application logic directly calls OpenAI, then local development becomes harder.

If every feature decides its own provider, then fallback, logging, retries, and provider errors become duplicated everywhere.

So the design needs a different mental model.

The application should say:

```text
I need summarization.
```

The infrastructure should decide:

```text
Use the configured provider-model route for summarization.
```

That is the core idea of provider abstraction.

## Why Provider Abstraction Matters

AI providers are external systems.

External systems fail, change, rate-limit, and behave differently from each other.

For example:

```text
Ollama
-> local model server
-> useful for local development
-> no cloud dependency
-> limited by local machine resources

OpenAI
-> hosted provider
-> useful for stronger cloud models
-> requires API key
-> may add cost, latency, and privacy considerations
```

Both can generate text, but they are not the same operationally.

If the rest of the application knows too much about either provider, the code becomes vendor-first.

The goal is capability-first design:

```text
Business feature: summarization
Provider option: Ollama
Provider option: OpenAI
Routing decision: configuration and policy
```

This lets the summarization feature stay stable even when the provider changes behind it.

## Why I Built This Provider Abstraction Myself

After building this project, I learned about LiteLLM.

LiteLLM already provides many of the things I was learning to build:

- one interface for many LLM providers
- OpenAI-compatible request and response formats
- proxy server option
- Python SDK option
- routing
- retries
- fallback
- load balancing
- budgets
- rate limits
- logging integrations
- guardrails
- virtual keys

At first, that made me wonder:

```text
Did I waste time building my own provider abstraction?
```

The answer is no.

There is a big difference between:

```text
using a tool
```

and:

```text
understanding the backend design problem the tool solves
```

LiteLLM can help teams move faster.

This project helped me understand why a tool like LiteLLM exists.

That understanding matters for backend engineering and AI platform interviews.

If someone asks:

```text
How would you design provider fallback?
How would you avoid vendor lock-in?
How would you prevent provider errors from leaking into business logic?
How would you decide whether local-to-cloud fallback is safe?
How would you structure model routing?
```

I can now explain the design from first principles.

That is the value of building it.

## Verified Provider Structure

The provider-related implementation is spread across these files:

```text
app/application/ai/domain/ai_model_port.py
app/application/ai/domain/ai_inference_port.py
app/application/ai/domain/embedding_port.py
app/application/ai/domain/ai_capability.py
app/application/ai/domain/ai_provider.py
app/application/ai/domain/model_registry.py
app/application/ai/infrastructure/ollama_adapter.py
app/application/ai/infrastructure/openai_adapter.py
app/application/ai/infrastructure/inference_router.py
app/application/ai/core/circuit_breakers.py
app/application/ai/core/openai_embedding_adapter.py
app/core/model_registry.py
app/core/retry.py
app/core/timeout.py
```

The split between abstraction and implementation is now explicit:

```text
app/application/ai/domain/ai_inference_port.py
```

contains the application-facing inference abstraction.

```text
app/application/ai/infrastructure/inference_router.py
```

contains the concrete `InferenceRouter`.

The domain file defines what the application needs.

The infrastructure file provides the implementation that applies routing and fallback.

## The Provider Port

The current text-generation provider contract lives in:

```text
app/application/ai/domain/ai_model_port.py
```

It defines:

```python
async def generate(
    self,
    *,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    ...
```

This interface says:

```text
Give me a prompt.
Give me generation settings.
Return generated text.
```

Both provider adapters implement this same contract:

```text
OllamaAdapter
OpenAIAdapter
```

That means the rest of the application does not need to know whether the text came from Ollama or OpenAI.

It receives only:

```text
str
```

Returning only `str` keeps the current implementation simple.

For this project, that is a good starting point because the summarization service only needs generated text.

Later, if the project needs deeper provider observability, the internal provider contract can evolve to preserve:

- token usage
- finish reason
- provider request ID
- model-specific metadata
- cost information

Conceptually, that future internal result object could look like this:

```python
class TextGenerationResult:
    text: str
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: str | None
    provider_request_id: str | None
```

The public API still would not need to expose all of that.

But internally, it would help with debugging, cost tracking, evaluation, and fallback analysis.

## Text Generation Is Not Embedding

One important design lesson:

> Do not force every AI capability through the same method.

Text generation and embeddings are different operations.

Text generation returns text:

```text
prompt -> generated text
```

Embeddings return vectors:

```text
text -> list of floats
```

So the project uses a separate embedding port:

```text
app/application/ai/domain/embedding_port.py
```

There is also an early `OpenAIEmbeddingAdapter`:

```text
app/application/ai/core/openai_embedding_adapter.py
```

That is groundwork for future RAG integration.

It is not part of the current `/ai/summarize` request lifecycle.

This distinction is important because RAG will need both:

```text
embedding
-> retrieval
-> context assembly
-> text generation
```

RAG is not just another provider.

It is an application workflow.

## Provider vs Model

Another concept that became clearer while building this:

```text
Provider != Model
```

A provider is the platform:

```text
Ollama
OpenAI
```

A model is the model identifier executed through that provider:

```text
tinyllama
gpt-4.1-mini
text-embedding-3-small
```

In the current implementation, `AIProvider` maps each provider to a default model name:

```text
ollama -> tinyllama
openai -> gpt-4.1-mini
```

That is enough for learning provider routing.

But a more mature registry would not only say:

```text
summarization -> openai
```

It would say something closer to:

```text
summarization
-> provider: openai
-> model: gpt-4.1-mini
-> max input tokens
-> max output tokens
-> cost class
-> privacy class
-> fallback eligibility
```

The current registry stores provider routes, not rich model metadata.

That means it does not yet store:

- cost class
- context window
- token pricing
- region or data residency
- enabled or disabled status
- provider health
- per-capability model parameters

Those are future production improvements.

## Capabilities

Capabilities live in:

```text
app/application/ai/domain/ai_capability.py
```

The current enum contains:

```python
class AICapability(str, Enum):
    SUMMARIZATION = "summarization"
    CHAT = "chat"
    EMBEDDING = "embedding"
```

The active public API in this series is summarization.

Chat has a pipeline registered internally, but there is no public chat route in this blog's request lifecycle.

Embedding is a separate capability and should not be modeled as:

```text
generate() -> str
```

This is why capability-first design matters.

Different capabilities may need different:

- provider contracts
- prompt formats
- output validation rules
- cache keys
- routing policies
- privacy policies

Summarization and embedding are both AI features, but they should not be squeezed into the same abstraction.

## Model Registry

The model registry lives in:

```text
app/core/model_registry.py
```

Its job is to describe which provider adapter is configured for each AI capability.

It does not call the model.

It does not build prompts.

It does not parse responses.

It simply answers:

```text
For this capability, what is the primary provider?
Is there a fallback provider?
Is the required adapter registered?
```

The settings model lives in:

```text
app/application/ai/domain/model_registry.py
```

The route shape is:

```python
class ModelRoute(BaseModel):
    primary: AIProvider
    fallback: AIProvider | None = None
```

The environment variable format uses Pydantic nested settings with `__`:

```env
AI__MODEL_REGISTRY__SUMMARIZATION__PRIMARY=ollama
AI__MODEL_REGISTRY__SUMMARIZATION__FALLBACK=openai
```

This means:

```text
For summarization:
  primary provider = Ollama
  fallback provider = OpenAI
```

Provider values are validated by the `AIProvider` enum.

If a route is missing, the registry raises a controlled `ServiceError`.

If a route points to a provider adapter that was not registered, the registry also raises a controlled `ServiceError`.

That is better than letting a raw `KeyError` leak out of the provider layer.

## Service Container

The service container wires provider infrastructure during application startup.

It lives in:

```text
app/application/ai/core/container.py
```

This is where concrete infrastructure is assembled.

It creates long-lived clients:

```text
httpx.AsyncClient for Ollama
AsyncOpenAI for OpenAI
Redis client for AI cache
```

The important part is that these clients are not created per request.

They are created once during application lifespan, reused across requests, and closed on shutdown.

That matters because client creation can involve connection pools, timeouts, and resource management.

OpenAI is registered only when a real API key is available.

That keeps local Ollama-only development simple.

Local development can use:

```text
Ollama + Redis + FastAPI
```

Cloud-capable development can add:

```text
OpenAI API key + OpenAI fallback route
```

## Inference Port

The application-facing inference abstraction lives in:

```text
app/application/ai/domain/ai_inference_port.py
```

It defines:

```python
async def generate(
    self,
    *,
    capability: AICapability,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    ...
```

The `SummaryService` depends on this abstraction.

That means the service asks for:

```text
capability = summarization
```

not:

```text
call Ollama
call OpenAI
call a specific SDK method
```

This is the dependency inversion principle in action.

High-level application workflow depends on an interface.

Low-level provider details live behind that interface.

## Inference Router

The concrete router is:

```text
app/application/ai/infrastructure/inference_router.py
```

It implements `AIInferencePort`.

The router coordinates provider selection and fallback.

The current flow is:

```text
receive capability
-> ask ModelRegistry for primary adapter
-> ask ModelRegistry for fallback adapter
-> call primary provider
-> if primary fails with fallback-eligible AIProviderError, call fallback
-> if fallback also fails, raise ServiceError
```

There is no separate `RoutingPolicy` class yet.

The routing policy is simple and embedded in the router:

```text
use configured primary first
use configured fallback once if the failure is eligible
```

That is enough for this learning implementation.

A larger production system may eventually separate routing policy into its own component.

That policy could consider:

- provider priority
- model cost
- tenant budget
- local-only requests
- latency preference
- context-window size
- provider health
- quota status
- data residency

For now, the router keeps the provider decision centralized and readable.

## Actual Summarization Provider Flow

For `/ai/summarize`, the provider part of the request looks like this:

```text
SummaryService
-> AIInferencePort.generate(...)
-> InferenceRouter.generate(...)
-> ModelRegistry.get_primary(SUMMARIZATION)
-> primary AIModelPort.generate(...)
-> OllamaAdapter or OpenAIAdapter
-> external provider
-> raw text result
-> SummaryService response pipeline
```

If the primary provider fails with a fallback-eligible provider error:

```text
InferenceRouter
-> ModelRegistry.get_fallback(SUMMARIZATION)
-> fallback AIModelPort.generate(...)
-> fallback provider
-> raw text result
```

The response pipeline still runs after the provider returns.

Fallback does not skip validation.

The model output is still untrusted until the response pipeline validates and scores it.

## Ollama Adapter

The Ollama adapter lives in:

```text
app/application/ai/infrastructure/ollama_adapter.py
```

It uses:

```text
httpx.AsyncClient
```

The configured default base URL is:

```text
http://ollama:11434
```

That hostname is useful inside Docker Compose because the FastAPI container can reach the Ollama container by service name.

For local development outside Docker, the `.env` can point to:

```text
http://localhost:11434
```

The adapter calls:

```text
POST /api/generate
```

The request payload includes:

```text
model
prompt
temperature
num_predict
stream = false
```

The important translation is:

```text
application max_tokens
-> Ollama num_predict
```

Ollama returns generated text in the `response` field.

The adapter extracts that field, strips the text, and returns it as a plain string.

It also maps Ollama transport and HTTP failures into `AIProviderError`.

That keeps Ollama-specific exception handling inside the adapter.

## OpenAI Adapter

The OpenAI adapter lives in:

```text
app/application/ai/infrastructure/openai_adapter.py
```

It uses:

```text
AsyncOpenAI
```

It calls the OpenAI Responses API:

```python
await self.client.responses.create(
    model=model,
    input=prompt,
    temperature=temperature,
    max_output_tokens=max_tokens,
)
```

The important translation is:

```text
application prompt
-> OpenAI input

application max_tokens
-> OpenAI max_output_tokens
```

The adapter reads:

```text
response.output_text
```

and returns it as a plain string.

OpenAI-specific exceptions are mapped inside the adapter:

```text
RateLimitError
APITimeoutError
APIConnectionError
AuthenticationError
PermissionDeniedError
BadRequestError
APIError
```

The rest of the application does not need to import or understand those SDK-specific classes.

## Provider Error Model

Different providers fail differently.

Ollama may fail because:

- the local server is down
- the model is not available
- the request times out
- the HTTP response is not successful
- the response is empty

OpenAI may fail because:

- the API key is invalid
- the request is malformed
- the provider is rate-limiting
- the request times out
- the SDK receives an API error
- the provider returns no output text

If every adapter exposes its own exception types, the router becomes vendor-aware.

That is exactly what provider abstraction is trying to avoid.

So provider adapters normalize failures into:

```text
AIProviderError
```

The normalized error includes:

```text
category
provider
model
fallback_eligible
```

The vendor-neutral categories include:

```text
timeout
network
rate_limit
unavailable
authentication
invalid_request
invalid_response
configuration
circuit_open
unknown
```

This lets the router ask a better question:

```text
Is this failure eligible for fallback?
```

instead of:

```text
Was this an OpenAI RateLimitError or an httpx TimeoutException?
```

## Fallback Policy

Fallback is useful, but it is not automatically safe.

The naive version is:

```text
any provider error
-> try another provider
```

That is too broad.

Some errors are temporary and fallback makes sense.

Examples:

```text
timeout
network failure
rate limit
provider unavailable
invalid provider response
open circuit
unknown provider failure
```

Some errors should not trigger fallback.

Examples:

```text
authentication failure
invalid request
configuration error
safety rejection
response validation failure after generation
application bug
```

Why?

Because fallback can change the behavior and risk profile of the request.

For example:

```text
Ollama local failure
-> OpenAI cloud fallback
```

That may change:

- privacy boundary
- data residency
- provider retention policy
- cost
- latency
- model behavior

In this project, local-to-cloud fallback happens only if OpenAI is explicitly configured as the fallback provider.

There is not yet a per-request privacy classification such as:

```text
local only
cloud allowed
restricted
public
```

For sensitive workloads, the correct fallback result may be:

```text
controlled failure
```

not:

```text
send the prompt to a cloud provider
```

This is one of the most important lessons in AI backend design:

> Reliability should not silently override privacy policy.

## Attempt Limits

Fallback and retries must be bounded.

Otherwise, a single user request can accidentally turn into many provider calls.

The current provider adapters use:

```text
app/core/retry.py
```

The infrastructure retry policy allows:

```text
up to 2 attempts per adapter generate call
```

The inference router supports:

```text
1 primary provider
1 optional fallback provider
```

For fallback-eligible failures that reach the provider, the worst-case external generation attempts are:

```text
2 primary attempts + 2 fallback attempts = 4 provider attempts
```

There is no unbounded fallback loop.

If the circuit is already open, the adapter blocks before making an external provider call.

This matters for:

- latency
- provider cost
- local model load
- user experience
- incident debugging

If a production system adds more fallback providers, it should also add an explicit total attempt budget.

## Circuit Breaker

The circuit breaker lives in:

```text
app/application/ai/core/circuit_breakers.py
```

It protects provider calls inside the adapters.

The states are:

```text
CLOSED
OPEN
HALF_OPEN
```

The idea is simple:

```text
CLOSED
-> provider calls are allowed

OPEN
-> provider calls are blocked temporarily

HALF_OPEN
-> one recovery probe is allowed
```

The service container creates separate breakers for Ollama and OpenAI:

```text
Ollama: failure_threshold = 3, recovery_timeout = 20 seconds
OpenAI: failure_threshold = 5, recovery_timeout = 30 seconds
```

This prevents the application from repeatedly calling a provider that is already known to be unhealthy.

The breaker is provider-scoped, not provider-model-scoped.

That is good enough for this project.

A larger system may need circuit breaker state per:

- provider
- model
- endpoint
- region
- tenant

## Retry, Timeout, and Fallback Ordering

It helped me to think about resilience as a sequence.

In this project, the practical order is:

```text
Summary use case timeout boundary
-> InferenceRouter selects primary
-> infra_retry wraps the adapter call
-> Provider adapter checks circuit breaker on each attempt
-> Provider adapter calls provider with HTTP/SDK timeout when the circuit allows it
-> adapter maps provider failures into AIProviderError
-> Router checks fallback eligibility
-> Router calls one configured fallback provider if allowed
-> final controlled error if all eligible attempts fail
```

There are two timeout layers:

```text
app/core/timeout.py
-> overall async use-case timeout using asyncio.wait_for(...)

provider client timeout
-> httpx.AsyncClient or AsyncOpenAI timeout from AI__TIMEOUT_SECONDS
```

This bounds the request, but there is not yet a dedicated total inference budget object shared across primary retry and fallback attempts.

That would be useful later.

For example:

```text
total inference budget = 30 seconds
primary attempt 1 = 8 seconds
primary attempt 2 = 8 seconds
fallback attempt 1 = 8 seconds
stop before exceeding budget
```

The current implementation is simpler than that, but the direction is clear.

## Cancellation Behavior

The code does not explicitly catch `asyncio.CancelledError`.

That is useful.

If a client disconnects or the request is cancelled, cancellation should not be treated like a normal provider failure.

Cancellation should not:

- trigger fallback
- count as provider failure
- open circuit breakers
- write cache entries

The broad adapter handlers catch normal `Exception` paths, while cancellation is not intentionally converted into `AIProviderError`.

## Concurrency and Backpressure

There is no explicit provider concurrency limiter yet.

The project does not currently define:

```text
per-provider semaphore
queue size
queue wait timeout
AI-specific 429 or 503 overload behavior
per-tenant quota
token budget
cost budget
```

This is an important production-readiness gap.

Ollama and OpenAI have different capacity profiles.

Ollama may be limited by:

- local CPU or GPU
- model size
- memory
- number of concurrent generations

OpenAI may be limited by:

- rate limits
- token limits
- budget
- tenant-level quotas

A production system should observe and limit them separately.

For example:

```text
Ollama semaphore: small local concurrency
OpenAI semaphore: provider quota-aware concurrency
Queue timeout: fail fast when capacity is exhausted
Overload response: 429 or 503 with safe retry guidance
```

That is not implemented yet, so I am treating it as roadmap work.

## Observability

Provider routing needs observability because provider decisions are otherwise hard to debug.

Useful questions during debugging:

- Which provider was selected?
- Which model was used?
- Did fallback happen?
- Why did fallback happen?
- Was the circuit open?
- Was the error a timeout, rate limit, or auth failure?
- How long did the provider call take?
- How many characters were sent?
- Did the output fail validation later?

The current provider routing logs include events such as:

```text
ai_router_primary_attempt
ai_router_primary_provider_failed
ai_router_fallback_attempt
ai_router_no_fallback_configured
ai_router_total_provider_failure
ai_inference_started
ai_inference_completed
ai_circuit_prevented_request
```

Provider logs include metadata such as:

```text
provider
model
latency_seconds
prompt_chars
status_code
error category
fallback eligibility
```

The normal success path logs prompt length and response length, not raw prompts or full raw responses.

That is important.

Provider-routing observability should record decisions, latency, usage, and failure categories without logging:

- API keys
- bearer tokens
- raw prompts
- raw model responses
- database credentials
- Redis credentials
- authorization headers

For production, I would also want:

- selected provider
- selected model
- retry count
- fallback reason
- total latency
- token usage
- cost estimate
- circuit state
- request ID

Some of that requires the provider result to preserve richer metadata than plain text.

## Safe Error Mapping

The safe error flow is:

```text
vendor exception
-> provider adapter maps it to AIProviderError
-> router checks fallback eligibility
-> fallback is attempted or skipped
-> final ServiceError or AI error reaches global exception handling
-> API client receives a safe error response
```

The API client should not receive:

- SDK exception details
- stack traces
- API keys
- provider credentials
- raw provider response payloads
- internal routing details

This is why provider adapters and global exception handlers are both important.

Adapters normalize provider-specific failures.

Exception handlers translate application failures into safe HTTP responses.

## Production-Oriented Design Lesson

This design is not vendor-first.

It is capability-first.

The application says:

```text
I need summarization.
```

The provider layer decides:

```text
Use the configured primary provider.
Fallback only when policy allows it.
Return a normalized result to the application.
```

Here is the responsibility table:

| Component | Responsibility |
| --- | --- |
| `AIModelPort` | Vendor-neutral text-generation contract |
| `EmbeddingPort` | Separate embedding contract for future RAG work |
| `OllamaAdapter` | Ollama-specific HTTP request and response handling |
| `OpenAIAdapter` | OpenAI Responses API request and response handling |
| `ModelRegistry` | Capability-to-provider route lookup |
| `InferenceRouter` | Primary execution and bounded fallback |
| `AIProviderError` | Vendor-neutral provider failure classification |
| `CircuitBreaker` | Temporarily blocks unhealthy provider calls |
| `infra_retry` | Retries eligible transient infrastructure failures |
| `timeout_from_self` | Bounds async use-case execution |

The most important separation is:

```text
ModelRegistry
-> describes configured routes

InferenceRouter
-> executes the route and applies fallback policy

ProviderAdapter
-> talks to the external provider
```

Keeping those responsibilities separate made the project easier to reason about.

## What I Learned

The provider abstraction helped me understand a deeper backend design idea:

> AI code should not be organized around vendors. It should be organized around capabilities and policies.

Ollama is one provider.

OpenAI is one provider.

The business feature is summarization.

The provider layer should make the best configured provider decision without leaking provider details into the application workflow.

The design is still intentionally simple, but the learning is real:

```text
ports protect the application
adapters isolate vendors
registry describes routing options
router applies provider execution policy
classified errors make fallback safer
resilience must be bounded
privacy policy matters as much as uptime
```
