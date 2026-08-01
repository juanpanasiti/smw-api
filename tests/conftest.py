"""
Integration test configuration.
Environment variables MUST be set before any src imports to avoid
pydantic-settings loading .env values ahead of the test overrides.
"""

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from dotenv import load_dotenv

# Load .env so we can respect user's custom passwords/users
load_dotenv()

db_user = os.environ.get("POSTGRES_USER", "postgres")
db_pass = os.environ.get("POSTGRES_PASSWORD", "postgres")
db_server = os.environ.get("POSTGRES_SERVER", "localhost")
db_port = os.environ.get("POSTGRES_TEST_PORT", "5433")
db_name = os.environ.get("POSTGRES_TEST_DB", "smw_api_test")

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = os.environ.get("REDIS_TEST_PORT", "6380")

# Set test env variables BEFORE any src module is imported,
# so pydantic-settings picks them up on first initialization.
os.environ["POSTGRES_USER"] = db_user
os.environ["POSTGRES_PASSWORD"] = db_pass
os.environ["POSTGRES_DB"] = db_name
os.environ["POSTGRES_SERVER"] = db_server
os.environ["POSTGRES_PORT"] = db_port
os.environ["REDIS_HOST"] = redis_host
os.environ["REDIS_PORT"] = redis_port

import httpx  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

from src.core.database import Base, get_db_session  # noqa: E402
from src.main import app  # noqa: E402

DATABASE_TEST_URL = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_server}:{db_port}/{db_name}"


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
async def db_session() -> AsyncGenerator[AsyncSession]:
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
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient]:
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


@pytest.fixture(autouse=True)
def mock_redis_globally(monkeypatch):
    monkeypatch.setattr("src.core.redis.redis_client.get", AsyncMock(return_value=None))
    monkeypatch.setattr("src.core.redis.redis_client.set", AsyncMock(return_value=None))
    monkeypatch.setattr("src.core.redis.redis_client.scan", AsyncMock(return_value=(0, [])))
    monkeypatch.setattr("src.core.redis.redis_client.delete", AsyncMock(return_value=None))
