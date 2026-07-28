"""
Associated Documentation: docs/integration_tests/test_category_update_with_expenses_blocked_400.md
"""

import datetime
import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_category, create_credit_card, next_month_date


@pytest.mark.asyncio
@pytest.mark.integration
async def test_category_update_with_expenses_blocked_400(client: AsyncClient, auth_headers: dict):
    """
    Attempt to update is_income on a category that has expenses associated with it.
    Verifies that the API returns 400 Bad Request with code CATEGORY_HAS_EXPENSES,
    while non-is_income updates (like name) remain allowed.
    """
    category_id = await create_category(client, auth_headers)
    account_id = await create_credit_card(client, auth_headers)

    today = datetime.date.today()
    first_payment = next_month_date()

    purchase_res = await client.post(
        "/api/v1/expenses/purchase",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "title": "Integration Purchase",
            "account_name": "Test Integration Card",
            "acquired_at": str(today),
            "amount": "1200.00",
            "first_payment_date": str(first_payment),
            "total_installments": 3,
            "description": "Integration test purchase",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert purchase_res.status_code == 201

    # Try to update is_income (expect 400)
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
