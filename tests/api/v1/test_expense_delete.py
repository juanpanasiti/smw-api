import datetime
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.expense import Expense, Payment


async def _create_credit_card(client: AsyncClient, headers: dict) -> str:
    res = await client.post(
        "/api/v1/accounts/credit-cards",
        json={
            "alias": f"Card {uuid.uuid4()}",
            "closing_day": 1,
            "due_day": 10,
            "limit": "5000.00",
            "financing_limit": "2500.00",
        },
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201
    return res.json()["data"]["id"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_purchase_with_installments_ok(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """
    Test deleting a Purchase expense that has associated installments (payments).
    Verifies that the expense and all its payments are removed from the database.
    """
    account_id = await _create_credit_card(client, auth_headers)

    today = datetime.date.today()
    next_month = today.replace(day=1) + datetime.timedelta(days=32)
    next_month = next_month.replace(day=10)

    # 1. Create a purchase with 3 installments
    res = await client.post(
        "/api/v1/expenses/purchase",
        json={
            "account_id": account_id,
            "title": "Purchase to delete",
            "account_name": "Test Card",
            "acquired_at": str(today),
            "amount": "300.00",
            "first_payment_date": str(next_month),
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
    # Need to expire or clear session cache first to get fresh results
    db_session.expire_all()

    exp_db_after = (await db_session.execute(stmt_exp)).scalars().first()
    assert exp_db_after is None

    payments_db_after = (await db_session.execute(stmt_pay)).scalars().all()
    assert len(payments_db_after) == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_subscription_ok(client: AsyncClient, auth_headers: dict, db_session: AsyncSession) -> None:
    """
    Test deleting a Subscription expense.
    Verifies that the subscription is removed from the database along with its empty installments list.
    """
    account_id = await _create_credit_card(client, auth_headers)

    today = datetime.date.today()
    next_month = today.replace(day=1) + datetime.timedelta(days=32)
    next_month = next_month.replace(day=10)

    # 1. Create a subscription
    res = await client.post(
        "/api/v1/expenses/subscription",
        json={
            "account_id": account_id,
            "title": "Subscription to delete",
            "account_name": "Test Card",
            "acquired_at": str(today),
            "amount": "15.99",
            "first_payment_date": str(next_month),
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
    assert len(payments_db) == 0  # Subscriptions don't generate explicit payments upfront

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
