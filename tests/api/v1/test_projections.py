import datetime
import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_projection_end_to_end(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test the end-to-end flow for credit card purchases and monthly projections.

    Verifies that:
    1. A new credit card can be created via POST /api/v1/accounts/credit-cards.
    2. A purchase expense split into multiple installments can be registered via POST /api/v1/expenses/purchase.
    3. The projection for the installment periods via GET /api/v1/projections/periods/{period}
       correctly calculates and lists the installment amounts.
    """
    # 1. Create a credit card
    card_res = await client.post(
        "/api/v1/accounts/credit-cards",
        json={
            "alias": "Test Integration Card",
            "closing_day": 1,
            "due_day": 10,
            "limit": "5000.00",
            "financing_limit": "2500.00",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert card_res.status_code == 201
    account_id = card_res.json()["data"]["id"]

    # 2. Create a purchase
    today = datetime.date.today()
    next_month = today.replace(day=1) + datetime.timedelta(days=32)
    next_month = next_month.replace(day=10)  # arbitrary day

    purchase_res = await client.post(
        "/api/v1/expenses/purchase",
        json={
            "account_id": account_id,
            "title": "Integration Purchase",
            "account_name": "Test Integration Card",
            "acquired_at": str(today),
            "amount": "1200.00",
            "first_payment_date": str(next_month),
            "total_installments": 3,
            "description": "Integration test purchase",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert purchase_res.status_code == 201

    # 3. Check projections for next_month
    period = f"{next_month.year}-{next_month.month:02d}"
    proj_res = await client.get(f"/api/v1/projections/periods/{period}", headers=auth_headers)
    assert proj_res.status_code == 200
    proj_data = proj_res.json()["data"]

    # 1200 / 3 = 400.00 should be the expense for that month
    assert proj_data["total_expenses"] == "400.00"

    # Verify that the payments list contains it
    assert len(proj_data["payments"]) > 0
    assert proj_data["payments"][0]["amount"] == "400.00"
