"""
Associated Documentation: docs/integration_tests/test_expense_delete_subscription_ok.md
"""

import datetime
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.expense import Expense, Payment
from tests.api.v1.helpers import create_credit_card, next_month_date


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_subscription_ok(client: AsyncClient, auth_headers: dict, db_session: AsyncSession) -> None:
    """
    Test deleting a Subscription expense.
    Verifies that the subscription is removed from the database along with its empty installments list.
    """
    account_id = await create_credit_card(client, auth_headers)

    today = datetime.date.today()
    first_payment = next_month_date()

    # 1. Create a subscription
    res = await client.post(
        "/api/v1/expenses/subscription",
        json={
            "account_id": account_id,
            "title": "Subscription to delete",
            "account_name": "Test Card",
            "acquired_at": str(today),
            "amount": "15.99",
            "first_payment_date": str(first_payment),
            "description": "Integration test subscription delete",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201
    expense_id = res.json()["data"]["id"]

    # 2. Verify in DB that subscription exists
    stmt_exp = select(Expense).where(Expense.id == expense_id)
    exp_db = (await db_session.execute(stmt_exp)).scalars().first()
    assert exp_db is not None

    stmt_pay = select(Payment).where(Payment.expense_id == expense_id)
    payments_db = (await db_session.execute(stmt_pay)).scalars().all()
    assert len(payments_db) == 0

    # 3. Delete the subscription
    del_res = await client.delete(
        f"/api/v1/expenses/{expense_id}",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert del_res.status_code == 200

    # 4. Verify in DB that subscription is deleted
    db_session.expire_all()

    exp_db_after = (await db_session.execute(stmt_exp)).scalars().first()
    assert exp_db_after is None

    payments_db_after = (await db_session.execute(stmt_pay)).scalars().all()
    assert len(payments_db_after) == 0
