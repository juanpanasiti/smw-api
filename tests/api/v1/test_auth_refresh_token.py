"""
Associated Documentation: docs/integration_tests/test_auth_refresh_token.md
"""

import uuid

import pytest
from httpx import AsyncClient


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
