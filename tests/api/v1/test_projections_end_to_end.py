"""
Associated Documentation: docs/integration_tests/test_projections_end_to_end.md
"""

import datetime
import uuid

import pytest
from httpx import AsyncClient

from tests.api.v1.helpers import create_credit_card, next_month_date


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
    account_id = await create_credit_card(client, auth_headers)

    first_payment = next_month_date()

    purchase_res = await client.post(
        "/api/v1/expenses/purchase",
        json={
            "account_id": account_id,
            "title": "Integration Purchase",
            "account_name": "Test Integration Card",
            "acquired_at": str(datetime.date.today()),
            "amount": "1200.00",
            "first_payment_date": str(first_payment),
            "total_installments": 3,
            "description": "Integration test purchase",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert purchase_res.status_code == 201

    period = f"{first_payment.year}-{first_payment.month:02d}"
    proj_res = await client.get(f"/api/v1/projections/periods/{period}", headers=auth_headers)
    assert proj_res.status_code == 200
    proj_data = proj_res.json()["data"]

    # 1200 / 3 = 400.00 should be the expense for that month
    assert proj_data["total_expenses"] == "400.00"

    # Verify that the payments list contains it
    assert len(proj_data["payments"]) > 0
    assert proj_data["payments"][0]["amount"] == "400.00"
