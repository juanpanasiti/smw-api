import contextlib

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.core.redis import get_redis_client


@pytest.mark.asyncio
async def test_get_db_session() -> None:
    """
    Test retrieving a database session from the dependency generator.

    Verifies that get_db_session yields a valid SQLAlchemy AsyncSession instance.
    """
    generator = get_db_session()
    session = await anext(generator)
    assert isinstance(session, AsyncSession)

    # Clean up generator
    with contextlib.suppress(StopAsyncIteration):
        await anext(generator)


@pytest.mark.asyncio
async def test_get_redis_client() -> None:
    """
    Test retrieving a Redis client from the dependency generator.

    Verifies that get_redis_client yields a valid Redis client instance.
    """
    generator = get_redis_client()
    client = await anext(generator)
    assert client is not None

    with contextlib.suppress(StopAsyncIteration):
        await anext(generator)
