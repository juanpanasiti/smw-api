"""
Associated Documentation: docs/integration_tests/test_purchase_payments_non_divisible_redistribution.md
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
async def test_purchase_payments_sum_equals_total_non_divisible_amount(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
) -> None:
    """
    Scenario: Create a purchase whose amount does NOT divide evenly across installments.
    Input: amount=100.00, total_installments=3 → 33.33 + 33.34 + 33.33 (decreasing-balance).
    Expected:
      - DB contains exactly 3 Payment rows and their amounts sum to exactly 100.00.
      - Dynamic redistribution on PATCH updates unconfirmed siblings.
      - Status locking (confirmed/paid) excludes locked siblings from redistribution.
      - Rejection (422) occurs when attempting to change an amount without unconfirmed siblings.
    """
    account_id = await create_credit_card(client, auth_headers)
    first_payment_date = next_month_date()
    total_amount = Decimal("100.00")
    total_installments = 3

    res = await client.post(
        "/api/v1/expenses/purchase",
        json={
            "account_id": account_id,
            "title": "Non-divisible purchase",
            "account_name": "Test Card",
            "acquired_at": str(datetime.date.today()),
            "amount": str(total_amount),
            "first_payment_date": str(first_payment_date),
            "total_installments": total_installments,
            "description": "Integration test: non-exact payment split",
        },
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code == 201, res.text
    expense_id = res.json()["data"]["id"]

    # --- Step 1: verify count and sum ---
    stmt = select(Payment).where(Payment.expense_id == expense_id)
    payments = (await db_session.execute(stmt)).scalars().all()

    assert len(payments) == total_installments

    payments_total = sum(p.amount for p in payments)
    assert payments_total == total_amount

    # --- Step 2: verify all installments are unconfirmed ---
    wrong_status = [p for p in payments if p.status != "unconfirmed"]
    assert not wrong_status

    # --- Step 3: change installment #1 amount via API and re-verify sum ---
    installment_1 = next(p for p in payments if p.no_installment == 1)
    patch_res = await client.patch(
        f"/api/v1/expenses/payments/{installment_1.id}",
        json={"amount": "33.35", "version_id": installment_1.version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert patch_res.status_code == 200, patch_res.text

    db_session.expire_all()
    payments_after = (await db_session.execute(stmt)).scalars().all()
    payments_after_sorted = sorted(payments_after, key=lambda p: p.no_installment)

    payments_total_after = sum(p.amount for p in payments_after_sorted)
    assert payments_total_after == total_amount

    assert payments_after_sorted[0].amount == Decimal("33.35")
    assert payments_after_sorted[1].amount == Decimal("33.32")
    assert payments_after_sorted[2].amount == Decimal("33.33")

    # --- Step 4: confirm installment #1 ---
    patch_status_res = await client.patch(
        f"/api/v1/expenses/payments/{installment_1.id}",
        json={"status": "confirmed", "version_id": payments_after_sorted[0].version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert patch_status_res.status_code == 200, patch_status_res.text
    assert patch_status_res.json()["data"]["status"] == "confirmed"

    # --- Step 5: change installment #2 amount to 33.33 ---
    patch_amt_res = await client.patch(
        f"/api/v1/expenses/payments/{payments_after_sorted[1].id}",
        json={"amount": "33.33", "version_id": payments_after_sorted[1].version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert patch_amt_res.status_code == 200, patch_amt_res.text

    db_session.expire_all()
    payments_final = (await db_session.execute(stmt)).scalars().all()
    payments_final_sorted = sorted(payments_final, key=lambda p: p.no_installment)

    payments_total_final = sum(p.amount for p in payments_final_sorted)
    assert payments_total_final == total_amount

    assert payments_final_sorted[0].amount == Decimal("33.35")
    assert payments_final_sorted[1].amount == Decimal("33.33")
    assert payments_final_sorted[2].amount == Decimal("33.32")
    assert payments_final_sorted[0].status == "confirmed"

    # --- Step 6: lock #1 and #2 (status 'paid'), try to change #3 ---
    await client.patch(
        f"/api/v1/expenses/payments/{payments_final_sorted[0].id}",
        json={"status": "paid", "version_id": payments_final_sorted[0].version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    await client.patch(
        f"/api/v1/expenses/payments/{payments_final_sorted[1].id}",
        json={"status": "paid", "version_id": payments_final_sorted[1].version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    db_session.expire_all()
    payments_before_step6 = sorted((await db_session.execute(stmt)).scalars().all(), key=lambda p: p.no_installment)
    patch_fail_res = await client.patch(
        f"/api/v1/expenses/payments/{payments_before_step6[2].id}",
        json={"amount": "10.00", "version_id": payments_before_step6[2].version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert patch_fail_res.status_code == 422
    error_data = patch_fail_res.json()["detail"]
    assert error_data["code"] == "PAYMENT_AMOUNT_EXCEEDS_PURCHASE_TOTAL"
    assert "No unconfirmed payments available" in error_data["message"]
