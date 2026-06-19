import contextlib

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.core.redis import get_redis_client


@pytest.mark.asyncio
async def test_get_db_session() -> None:
    generator = get_db_session()
    session = await anext(generator)
    assert isinstance(session, AsyncSession)

    # Clean up generator
    with contextlib.suppress(StopAsyncIteration):
        await anext(generator)


@pytest.mark.asyncio
async def test_get_redis_client() -> None:
    generator = get_redis_client()
    client = await anext(generator)
    assert client is not None

    with contextlib.suppress(StopAsyncIteration):
        await anext(generator)
