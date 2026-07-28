"""
Associated Documentation: docs/integration_tests/test_auth_registration_and_login.md
"""

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
