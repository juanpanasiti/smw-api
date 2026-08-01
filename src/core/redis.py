import uuid
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from src.core.config import settings

redis_client = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def get_redis_client() -> AsyncGenerator[aioredis.Redis]:
    yield redis_client


async def invalidate_user_projections(user_id: str | uuid.UUID) -> None:
    pattern = f"user:{user_id}:projections:*"
    cursor = 0
    first = True
    while cursor != 0 or first:
        first = False
        cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await redis_client.delete(*keys)
