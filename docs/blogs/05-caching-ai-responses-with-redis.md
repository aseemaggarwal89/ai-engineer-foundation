# 05 - Caching AI Responses with Redis in a FastAPI Backend

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


AI calls can be slow.

AI calls can also be expensive.

If two requests ask the same model to summarize the same text with the same settings, it often makes sense to reuse the previous response.

This project uses Redis to cache validated AI responses.

## Why Cache AI Responses?

Caching helps with:

- lower latency
- lower model cost
- fewer repeated provider calls
- better user experience
- less pressure on local models like Ollama

But AI caching needs careful design.

You should not cache blindly.

## Where Caching Happens

The caching workflow lives in:

```text
app/application/ai/services/summary_service.py
```

The cache implementation lives in:

```text
app/application/ai/infrastructure/redis_ai_cache.py
```

The service follows a cache-aside pattern:

```text
build prompt
-> build cache key
-> check Redis
-> if hit, return cached response
-> if miss, call model
-> validate response
-> store validated response
```

## Cache Key Design

The cache key is built from:

- capability
- prompt
- model
- temperature
- max tokens

Code:

```python
raw = f"{capability}|{model}|{temperature}|{max_tokens}|{prompt}"
hash_key = hashlib.sha256(raw.encode()).hexdigest()
return f"ai_cache:{hash_key}"
```

This matters because each of these fields can affect the answer.

Changing the model should create a different cache entry.

Changing temperature should create a different cache entry.

Changing the prompt should create a different cache entry.

## Why Hash the Key?

Prompts can be long.

Redis keys should stay compact and safe.

Instead of storing the full prompt in the key, the project hashes the key input with SHA-256.

That gives a stable compact key:

```text
ai_cache:2af42f...
```

## Cache Hit

If Redis has a value, the service logs:

```text
ai_cache_hit
```

Then it returns cached bullets:

```python
return json.loads(cached)
```

No model call is needed.

## Cache Miss

If Redis does not have a value, the service logs:

```text
ai_cache_miss
```

Then it calls the inference router:

```python
raw_output = await self.inference.generate(...)
```

After the model returns, the response still must pass validation before being cached.

## Cache Only Trusted Output

This is one of the most important design choices:

```python
await self.cache.set(cache_key, json.dumps(bullets), ttl=3600)
```

The service caches `bullets`, not raw model output.

That means Redis stores only the post-validated structured response.

This prevents bad model output from being reused accidentally.

## TTL Strategy

The current TTL is:

```python
ttl=3600
```

That means one hour.

For real applications, TTL depends on the use case:

- short TTL for changing content
- longer TTL for deterministic summaries
- no cache for personalized or sensitive output
- separate TTL per AI capability

## Redis in Docker Compose

The local stack includes Redis:

```yaml
redis:
  image: redis:7
  container_name: ai_engineer_redis
  ports:
    - "6379:6379"
```

The app connects using AI settings:

```env
AI__REDIS_HOST=redis
AI__REDIS_PORT=6379
```

Inside Docker Compose, `redis` is the service hostname.

If you run the app directly on your machine, you may use:

```env
AI__REDIS_HOST=localhost
```

## What Not To Cache

Be careful with:

- user-specific answers
- private data
- prompts containing secrets
- outputs that depend on current time
- outputs that depend on permissions
- outputs that should be audited

Caching can accidentally leak or reuse context if the cache key does not include all relevant dimensions.

## Better Cache Keys for Production

For production, consider adding:

- prompt version
- tenant ID
- user ID if output is personalized
- language
- feature name
- model provider
- safety policy version

Example:

```text
capability|tenant|prompt_version|model|temperature|max_tokens|prompt
```

## Observability

Useful cache metrics:

- cache hit count
- cache miss count
- Redis errors
- cache latency
- cache size
- model calls avoided

The project currently logs cache hits and misses.

That is a good first step.

## Final Thought

AI caching is not just an optimization.

It is part of the reliability and cost-control layer of an AI backend.

Cache the right thing, with the right key, after validation.
