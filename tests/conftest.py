"""
Integration test configuration.
Environment variables MUST be set before any src imports to avoid
pydantic-settings loading .env values ahead of the test overrides.
"""

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator

# Set test env variables BEFORE any src module is imported,
# so pydantic-settings picks them up on first initialization.
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "postgres_test_password"
os.environ["POSTGRES_DB"] = "smw_api_test"
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_PORT"] = "5433"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6380"

import httpx  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

from src.core.database import Base, get_db_session  # noqa: E402
from src.main import app  # noqa: E402

DATABASE_TEST_URL = "postgresql+asyncpg://postgres:postgres_test_password@localhost:5433/smw_api_test"


def _run_sync(coro):
    """Run an async coroutine synchronously in a fresh event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _create_tables():
    engine = create_async_engine(DATABASE_TEST_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def _drop_tables():
    engine = create_async_engine(DATABASE_TEST_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# Create tables once before any test module is executed
_run_sync(_create_tables())


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(DATABASE_TEST_URL, echo=False)
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: httpx.AsyncClient) -> dict[str, str]:
    uid = uuid.uuid4()
    email = f"test_{uid}@integration.com"
    password = "Password123!"
    # Register
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "profile": {
                "first_name": "Test",
                "last_name": "User",
                "birthdate": "1990-01-01",
                "monthly_spending_limit": "2000.00",
            },
        },
        headers={"Idempotency-Key": str(uid)},
    )
    assert res.status_code == 201, res.text
    # Login to obtain tokens
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


import pytest
from unittest.mock import AsyncMock

@pytest.fixture(autouse=True)
def mock_redis_globally(monkeypatch):
    monkeypatch.setattr("src.core.redis.redis_client.get", AsyncMock(return_value=None))
    monkeypatch.setattr("src.core.redis.redis_client.set", AsyncMock(return_value=None))
    monkeypatch.setattr("src.core.redis.redis_client.scan", AsyncMock(return_value=(0, [])))
    monkeypatch.setattr("src.core.redis.redis_client.delete", AsyncMock(return_value=None))
