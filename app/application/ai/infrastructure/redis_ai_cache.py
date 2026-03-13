import json
import hashlib
from redis.asyncio import Redis

from app.application.ai.domain.ai_cache_port import AIResponseCachePort


class RedisAIResponseCache(AIResponseCachePort):

    def __init__(self, redis: Redis):
        self.redis = redis

    def build_key(self, prompt: str, model: str) -> str:

        raw = f"{model}:{prompt}"
        return hasxhlib.sha256(raw.encode()).hexdigest()

    async def get(self, key: str):

        data = await self.redis.get(key)

        if not data:
            return None

        return json.loads(data)

    async def set(self, key: str, value: str, ttl: int = 3600):

        await self.redis.set(key, json.dumps(value), ex=ttl)