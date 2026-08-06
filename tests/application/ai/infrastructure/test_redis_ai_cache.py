from app.application.ai.infrastructure.redis_ai_cache import RedisAIResponseCache


def test_cache_key_hashes_prompt_instead_of_storing_raw_input():
    cache = RedisAIResponseCache(redis=None)

    key = cache.build_key(
        namespace="test",
        capability="summarization",
        prompt="v1|Summarize: customer private text",
        model_identity="primary=ollama:tinyllama;fallback=none",
        temperature=0.6,
        max_tokens=512,
        schema_version=1,
    )

    assert key.startswith("ai_cache:test:v1:")
    assert "customer private text" not in key


def test_cache_key_changes_when_behavior_settings_change():
    cache = RedisAIResponseCache(redis=None)
    common = {
        "namespace": "test",
        "capability": "summarization",
        "prompt": "v1|Summarize: text",
        "model_identity": "primary=ollama:tinyllama;fallback=none",
        "temperature": 0.6,
        "max_tokens": 512,
        "schema_version": 1,
    }

    original_key = cache.build_key(**common)
    changed_model_key = cache.build_key(
        **{
            **common,
            "model_identity": "primary=openai:gpt-4.1-mini;fallback=none",
        }
    )
    changed_temperature_key = cache.build_key(**{**common, "temperature": 0.2})
    changed_schema_key = cache.build_key(**{**common, "schema_version": 2})
    changed_namespace_key = cache.build_key(**{**common, "namespace": "prod"})

    assert changed_model_key != original_key
    assert changed_temperature_key != original_key
    assert changed_schema_key != original_key
    assert changed_namespace_key != original_key
