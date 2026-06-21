import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_auth_registration_and_login(client: AsyncClient):
    """
    Test user registration and subsequent login integration flow.

    Verifies that:
    1. A new user can be registered via POST /api/v1/auth/register.
    2. The registered user can log in via POST /api/v1/auth/login using their credentials,
       successfully returning an access token and a refresh token.
    """
    uid = uuid.uuid4()

    # Registration returns UserResponseSchema (no tokens)
    payload = {
        "email": f"integration_{uid}@test.com",
        "password": "Password123!",
        "profile": {
            "first_name": "Integration",
            "last_name": "Test",
            "birthdate": "1990-01-01",
            "monthly_spending_limit": "5000.00",
        },
    }

    res = await client.post(
        "/api/v1/auth/register",
        json=payload,
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["email"] == f"integration_{uid}@test.com"
    assert data["role"] == "user"

    # Login returns Token (access_token + refresh_token)
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": f"integration_{uid}@test.com", "password": "Password123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_res.status_code == 200, login_res.text
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

@pytest.mark.asyncio
@pytest.mark.integration
async def test_auth_refresh_token(client: AsyncClient):
    uid = uuid.uuid4()
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"refresh_{uid}@test.com",
            "password": "Password123!",
            "profile": {
                "first_name": "Refresh",
                "last_name": "Test",
                "birthdate": "1990-01-01",
                "monthly_spending_limit": "1000.00",
            },
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    # Login
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": f"refresh_{uid}@test.com", "password": "Password123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    tokens = login_res.json()
    old_refresh_token = tokens["refresh_token"]

    # Refresh
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert refresh_res.status_code == 200, refresh_res.text
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # Invalid Refresh
    invalid_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token_string"},
    )
    assert invalid_res.status_code == 401
    assert invalid_res.json()["detail"]["error"]["code"] == "INVALID_REFRESH_TOKEN"
