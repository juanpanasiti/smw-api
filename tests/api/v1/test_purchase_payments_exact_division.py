"""
Associated Documentation: docs/integration_tests/test_purchase_payments_exact_division.md
"""

import datetime
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.expense import Payment
from tests.api.v1.helpers import create_credit_card, next_month_date


@pytest.mark.asyncio
@pytest.mark.integration
async def test_purchase_payments_sum_equals_total_exact_division(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
) -> None:
    """
    Scenario: Create a purchase with an amount that divides evenly across installments.
    Input: amount=1200.00, total_installments=3 → each installment should be 400.00.
    Expected:
      - DB contains exactly 3 Payment rows whose amounts sum to exactly 1200.00.
      - All installments have status="unconfirmed".
    """
    account_id = await create_credit_card(client, auth_headers)
    first_payment_date = next_month_date()
    total_amount = Decimal("1200.00")
    total_installments = 3

    res = await client.post(
        "/api/v1/expenses/purchase",
        json={
            "account_id": account_id,
            "title": "Laptop — exact division",
            "account_name": "Test Card",
            "acquired_at": str(datetime.date.today()),
            "amount": str(total_amount),
            "first_payment_date": str(first_payment_date),
            "total_installments": total_installments,
            "description": "Integration test: exact payment split",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    expense_id = res.json()["data"]["id"]

    stmt = select(Payment).where(Payment.expense_id == expense_id)
    payments = (await db_session.execute(stmt)).scalars().all()

    assert len(payments) == total_installments

    payments_total = sum(p.amount for p in payments)
    assert payments_total == total_amount, f"Expected payments to sum to {total_amount}, got {payments_total}"

    unconfirmed = [p for p in payments if p.status != "unconfirmed"]
    assert not unconfirmed, (
        f"Expected all installments to have status='unconfirmed', "
        f"but found: {[(p.no_installment, p.status) for p in unconfirmed]}"
    )
