from app.application.ai.infrastructure.redis_ai_cache import RedisAIResponseCache


def test_cache_key_hashes_prompt_instead_of_storing_raw_input():
    cache = RedisAIResponseCache(redis=None)

    key = cache.build_key(
        capability="summarization",
        prompt="v1|Summarize: customer private text",
        model="tinyllama",
        temperature=0.6,
        max_tokens=512,
    )

    assert key.startswith("ai_cache:")
    assert "customer private text" not in key


def test_cache_key_changes_when_model_settings_change():
    cache = RedisAIResponseCache(redis=None)
    common = {
        "capability": "summarization",
        "prompt": "v1|Summarize: text",
        "model": "tinyllama",
        "temperature": 0.6,
        "max_tokens": 512,
    }

    original_key = cache.build_key(**common)
    changed_model_key = cache.build_key(**{**common, "model": "gpt-4.1-mini"})
    changed_temperature_key = cache.build_key(**{**common, "temperature": 0.2})

    assert changed_model_key != original_key
    assert changed_temperature_key != original_key
