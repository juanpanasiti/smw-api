from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.core.redis import get_redis_client

# Dependencia para obtener la sesión de BD
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# Dependencia para obtener el cliente de Redis
RedisClient = Annotated[aioredis.Redis, Depends(get_redis_client)]
