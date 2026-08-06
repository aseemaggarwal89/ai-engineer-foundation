import hashlib
from redis.asyncio import Redis

from app.application.ai.domain.ai_cache_port import AIResponseCachePort


class RedisAIResponseCache(AIResponseCachePort):

    def __init__(self, redis: Redis):
        self.redis = redis

    def build_key(self, *,
                  namespace: str,
                  capability: str,
                  prompt: str,
                  model_identity: str,
                  temperature: float,
                  max_tokens: int,
                  schema_version: int) -> str:
        raw = (
            f"{namespace}|v{schema_version}|{capability}|{model_identity}|"
            f"{temperature}|{max_tokens}|{prompt}"
        )
        hash_key = hashlib.sha256(raw.encode()).hexdigest()

        return f"ai_cache:{namespace}:v{schema_version}:{hash_key}"

    async def get(self, key: str):
        return await self.redis.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600):
        await self.redis.set(key, value, ex=ttl)
