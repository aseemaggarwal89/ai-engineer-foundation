# Guardrails for AI APIs: Validating Prompts and Model Responses

AI APIs need guardrails on both sides of the model call.

You need to validate what users send into the system.

You also need to validate what the model sends back.

This project uses both request-side and response-side guardrails.

## Why Guardrails Matter

Without guardrails, an AI endpoint can become fragile:

- users can send empty prompts
- users can send very large prompts
- users can send binary or malformed data
- prompts can contain sensitive data
- models can return empty responses
- models can return malformed text
- models can return refusal boilerplate
- models can return output that does not match your API contract

A good AI backend should treat both user input and model output as untrusted.

## Request-Side Guardrails

The summarization use case runs request-side checks before prompt construction:

```text
app/application/ai/usecases/summarize_text.py
```

The flow is:

```python
self.safety.check(text)
text = self.guardrails.validate_prompt(text)
```

There are two parts:

- `AISafetyFilter`
- `AIGuardrails`

## Sensitive Data Filter

The safety filter lives in:

```text
app/application/ai/validator/request/ai_safety.py
```

It blocks obvious sensitive terms:

```python
BLOCKED_TERMS = {
    "credit card",
    "cvv",
    "password",
    "ssn",
}
```

If a blocked term appears, the system raises a request validation error before calling the model.

This is a simple first version. In a real production system, you may replace or extend this with:

- PII detection
- secret scanning
- allowlists
- user-specific data policy
- audit logging

## Prompt Guardrails

The prompt guardrails live in:

```text
app/application/ai/validator/request/ai_guardrails.py
```

They handle:

- empty prompts
- hard prompt size limits
- binary/control character detection
- text sanitization
- whitespace normalization
- soft truncation

The idea is simple:

> Do not spend AI provider time or money on bad input.

## Hard Limit vs Soft Limit

The project separates hard rejection from soft truncation.

A hard limit protects infrastructure:

```python
if len(value) > HARD_LIMIT:
    raise PromptTooLargeError()
```

A soft limit protects cost:

```python
if len(value) > SOFT_LIMIT:
    value = value[:SOFT_LIMIT]
```

This gives you two controls:

- reject input that is too large to safely handle
- trim input that is acceptable but too expensive

## Response-Side Validation

The model response is validated in:

```text
app/application/ai/validator/response/response_validator.py
```

The validator rejects:

- empty output
- suspiciously short output
- prompt leakage
- malformed code-fence-heavy output

Example:

```python
if not summary:
    raise ResponseValidationError("Empty AI response")
```

This matters because a successful provider HTTP response does not guarantee useful model content.

## Parsing AI Output

For summarization, the model is expected to return bullet points.

The parser lives in:

```text
app/application/ai/core/bullet_parser.py
```

It converts raw model text into a Python list:

```python
lines = [line.strip("-• ").strip() for line in text.splitlines()]
return [line for line in lines if line]
```

This turns model text into application data.

## Validating Structured Output

After parsing, the pipeline validates the bullet list:

```python
valid_bullets = self.validator.validate_bullets(bullets)
```

This prevents returning invalid structured output to API clients.

The current implementation also clamps the response:

```python
return bullets[:5]
```

That keeps the API contract predictable.

## Hallucination Guard

The hallucination guard lives in:

```text
app/application/ai/validator/response/hallucination_guard.py
```

The current guard is simple: it rejects bullets that are too long.

That may sound basic, but it creates an extension point.

Later, this can become:

- source-grounding checks
- semantic similarity checks
- citation validation
- retrieval-backed verification
- LLM-as-judge evaluation

## Response Scoring

The scorer lives in:

```text
app/application/ai/validator/response/response_scorer.py
```

The summarization scorer gives a quality score based on:

- whether bullets exist
- average bullet length
- number of bullets

The service rejects output below a threshold:

```python
if score < self.threshold:
    raise ResponseValidationError("Low quality AI output")
```

This is a lightweight quality gate.

## Chat Pipeline Guardrails

The chat pipeline is less structured than summarization.

It lives in:

```text
app/application/ai/core/chat_pipeline.py
```

It does:

```text
raw text
-> normalize
-> validate
-> refusal guard
-> score
```

The refusal guard catches common phrases such as:

- `I cannot assist`
- `I can't help`
- `I'm unable to`

This gives chat responses a basic reliability layer too.

## Best Practices

When designing AI guardrails:

- validate input before building prompts
- keep provider calls behind size and safety checks
- treat model output as untrusted
- parse model text into typed application data
- validate after parsing
- reject low-quality output
- log metadata, not sensitive prompt content
- write unit tests for both accepted and rejected paths

## Final Thought

Guardrails are not only about safety.

They are also about reliability, cost control, and predictable API behavior.

If your backend cannot trust user input or model output, guardrails are the system that stands between chaos and a clean API contract.

