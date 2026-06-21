import uuid

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_category(client: AsyncClient, headers: dict) -> str:
    """Creates a movement category and returns its ID."""
    res = await client.post(
        "/api/v1/categories/",
        json={"name": f"Bill Category {uuid.uuid4()}", "is_income": False},
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


async def _create_bill_service(client: AsyncClient, headers: dict, category_id: str) -> str:
    """Creates a bill service and returns its ID."""
    res = await client.post(
        "/api/v1/bills/services",
        json={
            "category_id": category_id,
            "name": "Electricity",
            "service_type": "utility",
            "expected_arrival_day": 10,
            "is_active": True,
        },
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


async def _register_and_login(client: AsyncClient) -> dict:
    """Registers a new user and returns auth headers."""
    uid = uuid.uuid4()
    email = f"user_{uid}@test.com"
    password = "Password123!"
    await client.post(
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
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_service_update_full(client: AsyncClient, auth_headers: dict):
    """
    Full update: all five updatable fields are sent in the request body.

    Verifies that every field is persisted and returned correctly in the response.
    """
    category_id = await _create_category(client, auth_headers)
    new_category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)

    res = await client.patch(
        f"/api/v1/bills/services/{service_id}",
        json={
            "category_id": new_category_id,
            "name": "Electricity Updated",
            "service_type": "electric",
            "expected_arrival_day": 20,
            "is_active": False,
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["id"] == service_id
    assert data["category_id"] == new_category_id
    assert data["name"] == "Electricity Updated"
    assert data["service_type"] == "electric"
    assert data["expected_arrival_day"] == 20
    assert data["is_active"] is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_service_update_partial(client: AsyncClient, auth_headers: dict):
    """
    Partial update: only a subset of fields is sent.

    Verifies that only the provided fields change while the rest retain their
    original values.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)

    # Update only name and is_active
    res = await client.patch(
        f"/api/v1/bills/services/{service_id}",
        json={"name": "Partial Name", "is_active": False},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["name"] == "Partial Name"
    assert data["is_active"] is False
    # Fields not included in the request must remain unchanged
    assert data["service_type"] == "utility"
    assert data["expected_arrival_day"] == 10
    assert data["category_id"] == category_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_service_update_empty_body_returns_422(client: AsyncClient, auth_headers: dict):
    """
    Empty body: no fields are provided.

    Verifies that Pydantic's @model_validator rejects the request with 422
    and includes the expected validation message.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)

    res = await client.patch(
        f"/api/v1/bills/services/{service_id}",
        json={},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 422, res.text
    assert "At least one field must be provided for update" in res.text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_service_update_not_found_returns_404(client: AsyncClient, auth_headers: dict):
    """
    Non-existent service ID.

    Verifies that attempting to update a service that does not exist returns
    404 with the BILL_SERVICE_NOT_FOUND error code.
    """
    non_existent_id = uuid.uuid4()

    res = await client.patch(
        f"/api/v1/bills/services/{non_existent_id}",
        json={"name": "Ghost Service"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 404, res.text
    assert res.json()["detail"]["error"]["code"] == "BILL_SERVICE_NOT_FOUND"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_service_update_other_user_returns_404(client: AsyncClient, auth_headers: dict):
    """
    Cross-user access: user B tries to update a service owned by user A.

    Verifies that the ownership check returns 404 (not 403) to avoid leaking
    information about resource existence.
    """
    # User A creates a service
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)

    # User B registers and logs in
    user_b_headers = await _register_and_login(client)

    res = await client.patch(
        f"/api/v1/bills/services/{service_id}",
        json={"name": "Hijacked"},
        headers={**user_b_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 404, res.text
    assert res.json()["detail"]["error"]["code"] == "BILL_SERVICE_NOT_FOUND"
