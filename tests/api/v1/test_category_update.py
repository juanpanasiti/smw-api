import datetime
import uuid

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_update_scenarios(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create a category
    create_res = await client.post(
        "/api/v1/categories/",
        json={"name": "Test Category", "description": "Original description", "is_income": False},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert create_res.status_code == 201
    category_id = create_res.json()["data"]["id"]

    # Scenario 1: Total update (3 fields)
    update_res_total = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Updated Category", "description": "Updated description", "is_income": True},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_total.status_code == 200
    data = update_res_total.json()["data"]
    assert data["name"] == "Updated Category"
    assert data["description"] == "Updated description"
    assert data["is_income"] is True

    # Scenario 2: Partial update (1 field)
    update_res_partial = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Partially Updated Category"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_partial.status_code == 200
    data = update_res_partial.json()["data"]
    assert data["name"] == "Partially Updated Category"
    assert data["description"] == "Updated description"  # should remain unchanged
    assert data["is_income"] is True  # should remain unchanged

    # Scenario 4: Empty payload (422 error)
    # The payload is effectively empty for the update schema if we pass {}
    # but Pydantic BaseModel by default might accept it if all are optional,
    # but our validator requires at least one.
    update_res_empty = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_empty.status_code == 422
    assert "At least one field must be provided for update" in update_res_empty.text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_update_with_expenses(client: AsyncClient, auth_headers: dict[str, str]):
    # 1. Create a category
    create_cat_res = await client.post(
        "/api/v1/categories/",
        json={"name": "Category with expenses", "description": "Original", "is_income": False},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert create_cat_res.status_code == 201
    category_id = create_cat_res.json()["data"]["id"]

    # 2. Create an account
    card_res = await client.post(
        "/api/v1/accounts/credit-cards",
        json={
            "alias": "Test Integration Card 2",
            "closing_day": 1,
            "due_day": 10,
            "limit": "5000.00",
            "financing_limit": "2500.00",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert card_res.status_code == 201
    account_id = card_res.json()["data"]["id"]

    # 3. Create an expense tied to this category
    today = datetime.date.today()
    next_month = today.replace(day=1) + datetime.timedelta(days=32)
    next_month = next_month.replace(day=10)

    purchase_res = await client.post(
        "/api/v1/expenses/purchase",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "title": "Integration Purchase",
            "account_name": "Test Integration Card 2",
            "acquired_at": str(today),
            "amount": "1200.00",
            "first_payment_date": str(next_month),
            "total_installments": 3,
            "description": "Integration test purchase",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert purchase_res.status_code == 201

    # Scenario 3: Try to update is_income (expect 400)
    update_res_error = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"is_income": True},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_error.status_code == 400
    error_data = update_res_error.json()["detail"]["error"]
    assert error_data["code"] == "CATEGORY_HAS_EXPENSES"
    assert error_data["message"] == "Cannot update is_income because there are expenses associated with this category."

    # Try to update name only (should succeed despite having expenses)
    update_res_success = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "New Name"},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_success.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_update_permissions(client: AsyncClient, auth_headers: dict[str, str]):
    # Register and login a second user
    uid = uuid.uuid4()
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user2_{uid}@test.com",
            "password": "Password123!",
            "profile": {
                "first_name": "User",
                "last_name": "Two",
                "birthdate": "1990-01-01",
                "monthly_spending_limit": "5000.00",
            },
        },
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": f"user2_{uid}@test.com", "password": "Password123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    user2_token = login_res.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # User 1 creates a category
    create_res = await client.post(
        "/api/v1/categories/",
        json={"name": "User 1 Category", "is_income": False},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert create_res.status_code == 201
    category_id = create_res.json()["data"]["id"]

    # Scenario 5: User 2 tries to update User 1's category (expect 403)
    update_res_403 = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Hacked"},
        headers={**user2_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert update_res_403.status_code == 403
    assert update_res_403.json()["detail"]["error"]["code"] == "FORBIDDEN_OPERATION"
