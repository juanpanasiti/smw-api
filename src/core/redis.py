from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from src.core.config import settings

redis_client = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True
)

async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    yield redis_client
