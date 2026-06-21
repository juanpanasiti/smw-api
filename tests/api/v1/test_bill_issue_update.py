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
        json={"name": f"Issue Cat {uuid.uuid4()}", "is_income": False},
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
            "name": f"Service {uuid.uuid4()}",
            "service_type": "utility",
            "expected_arrival_day": 10,
            "is_active": True,
        },
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


async def _create_bill_issue(
    client: AsyncClient,
    headers: dict,
    service_id: str,
    period: str = "2025-01",
    amount: str = "150.00",
    due_date: str = "2025-01-15",
) -> str:
    """Creates a bill issue and returns its ID."""
    res = await client.post(
        "/api/v1/bills/issues",
        json={
            "bill_service_id": service_id,
            "period": period,
            "amount": amount,
            "due_date": due_date,
        },
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["id"]


async def _register_and_login(client: AsyncClient) -> dict:
    """Registers a new user and returns auth headers."""
    uid = uuid.uuid4()
    email = f"issue_user_{uid}@test.com"
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
async def test_bill_issue_update_full(client: AsyncClient, auth_headers: dict):
    """
    Full update: all four updatable fields are sent in a single request.

    Verifies that every field is persisted and returned correctly in the response.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(client, auth_headers, service_id, period="2025-03")

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={
            "amount": "299.99",
            "due_date": "2025-03-20",
            "period": "2025-04",
            "status": "cancelled",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["id"] == issue_id
    assert data["amount"] == "299.99"
    assert data["due_date"] == "2025-03-20"
    assert data["period"] == "2025-04"
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_partial_amount(client: AsyncClient, auth_headers: dict):
    """
    Partial update: only amount is changed.

    Verifies that non-provided fields retain their original values.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(
        client, auth_headers, service_id, period="2025-05", amount="100.00", due_date="2025-05-10"
    )

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"amount": "999.50"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["amount"] == "999.50"
    assert data["period"] == "2025-05"
    assert data["due_date"] == "2025-05-10"
    assert data["status"] == "unpaid"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_partial_status(client: AsyncClient, auth_headers: dict):
    """
    Partial update: only status is changed to 'cancelled'.

    Verifies the status is updated and all other fields remain unchanged.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(
        client, auth_headers, service_id, period="2025-06", amount="200.00", due_date="2025-06-15"
    )

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"status": "cancelled"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["status"] == "cancelled"
    assert data["amount"] == "200.00"
    assert data["due_date"] == "2025-06-15"
    assert data["period"] == "2025-06"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_partial_due_date(client: AsyncClient, auth_headers: dict):
    """
    Partial update: only due_date is changed.

    Verifies that the due date is updated while all other fields remain intact.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(
        client, auth_headers, service_id, period="2025-07", amount="50.00", due_date="2025-07-05"
    )

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"due_date": "2025-07-25"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["due_date"] == "2025-07-25"
    assert data["period"] == "2025-07"
    assert data["amount"] == "50.00"
    assert data["status"] == "unpaid"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_partial_period(client: AsyncClient, auth_headers: dict):
    """
    Partial update: only period is changed to a non-conflicting value.

    Verifies that the period is updated successfully when no other issue for
    the same service occupies the new period.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(
        client, auth_headers, service_id, period="2025-08", amount="75.00", due_date="2025-08-10"
    )

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"period": "2025-09"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["period"] == "2025-09"
    assert data["amount"] == "75.00"
    assert data["status"] == "unpaid"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_empty_body_returns_422(client: AsyncClient, auth_headers: dict):
    """
    Empty body: no fields are provided.

    Verifies that Pydantic's @model_validator rejects the request with 422
    and includes the expected validation message.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(client, auth_headers, service_id, period="2025-10")

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 422, res.text
    assert "At least one field must be provided for update" in res.text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_paid_returns_409(client: AsyncClient, auth_headers: dict):
    """
    Paid-issue guard: attempt to update a bill issue that is in 'paid' status.

    Verifies that the service rejects the request with 409 and the
    BILL_ISSUE_ALREADY_PAID error code.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(
        client, auth_headers, service_id, period="2025-11", amount="120.00", due_date="2025-11-15"
    )

    # Force the issue into 'paid' status via a direct partial update
    # (simulates a scenario where status was set to paid without going through pay_issue)
    force_res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"status": "paid"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert force_res.status_code == 200, force_res.text

    # Now attempt to modify the already-paid issue
    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"amount": "999.00"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 409, res.text
    assert res.json()["detail"]["code"] == "BILL_ISSUE_ALREADY_PAID"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_period_conflict_returns_409(client: AsyncClient, auth_headers: dict):
    """
    Period conflict: the target period is already used by another issue of the same service.

    Verifies that the service rejects the update with 409 and the
    BILL_ISSUE_PERIOD_CONFLICT error code.
    """
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)

    # Create two issues for the same service in different periods
    issue_id = await _create_bill_issue(
        client, auth_headers, service_id, period="2026-01", amount="100.00", due_date="2026-01-15"
    )
    await _create_bill_issue(
        client, auth_headers, service_id, period="2026-02", amount="100.00", due_date="2026-02-15"
    )

    # Attempt to move issue_id to 2026-02, which is already taken
    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"period": "2026-02"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 409, res.text
    assert res.json()["detail"]["code"] == "BILL_ISSUE_PERIOD_CONFLICT"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_not_found_returns_404(client: AsyncClient, auth_headers: dict):
    """
    Non-existent issue ID.

    Verifies that attempting to update an issue that does not exist returns 404.
    """
    non_existent_id = uuid.uuid4()

    res = await client.patch(
        f"/api/v1/bills/issues/{non_existent_id}",
        json={"amount": "50.00"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 404, res.text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bill_issue_update_other_user_returns_404(client: AsyncClient, auth_headers: dict):
    """
    Cross-user access: user B tries to update a bill issue owned by user A.

    Verifies that the ownership check returns 404 (not 403) to avoid leaking
    information about resource existence.
    """
    # User A creates a service and an issue
    category_id = await _create_category(client, auth_headers)
    service_id = await _create_bill_service(client, auth_headers, category_id)
    issue_id = await _create_bill_issue(
        client, auth_headers, service_id, period="2026-03", amount="80.00", due_date="2026-03-10"
    )

    # User B registers and logs in
    user_b_headers = await _register_and_login(client)

    res = await client.patch(
        f"/api/v1/bills/issues/{issue_id}",
        json={"amount": "1.00"},
        headers={**user_b_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    assert res.status_code == 404, res.text
