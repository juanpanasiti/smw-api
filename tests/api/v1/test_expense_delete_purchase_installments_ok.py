"""
Associated Documentation: docs/integration_tests/test_expense_delete_purchase_installments_ok.md
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
async def test_delete_purchase_with_installments_ok(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """
    Test deleting a Purchase expense that has associated installments (payments).
    Verifies that the expense and all its payments are removed from the database.
    """
    account_id = await create_credit_card(client, auth_headers)

    today = datetime.date.today()
    first_payment = next_month_date()

    # 1. Create a purchase with 3 installments
    res = await client.post(
        "/api/v1/expenses/purchase",
        json={
            "account_id": account_id,
            "title": "Purchase to delete",
            "account_name": "Test Card",
            "acquired_at": str(today),
            "amount": "300.00",
            "first_payment_date": str(first_payment),
            "total_installments": 3,
            "description": "Integration test purchase delete",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201
    expense_id = res.json()["data"]["id"]

    # 2. Verify in DB that expense and 3 payments exist
    stmt_exp = select(Expense).where(Expense.id == expense_id)
    exp_db = (await db_session.execute(stmt_exp)).scalars().first()
    assert exp_db is not None

    stmt_pay = select(Payment).where(Payment.expense_id == expense_id)
    payments_db = (await db_session.execute(stmt_pay)).scalars().all()
    assert len(payments_db) == 3

    # 3. Delete the expense
    del_res = await client.delete(
        f"/api/v1/expenses/{expense_id}",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert del_res.status_code == 200

    # 4. Verify in DB that both expense and payments are deleted
    db_session.expire_all()

    exp_db_after = (await db_session.execute(stmt_exp)).scalars().first()
    assert exp_db_after is None

    payments_db_after = (await db_session.execute(stmt_pay)).scalars().all()
    assert len(payments_db_after) == 0
