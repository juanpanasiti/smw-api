import datetime
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.expense import Payment


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


def _next_month_date() -> datetime.date:
    today = datetime.date.today()
    first_of_next = today.replace(day=1) + datetime.timedelta(days=32)
    return first_of_next.replace(day=10)


# ---------------------------------------------------------------------------
# Test 1: exact division — payments sum must equal the total purchase amount
# ---------------------------------------------------------------------------
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
    account_id = await _create_credit_card(client, auth_headers)
    first_payment_date = _next_month_date()
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
    assert payments_total == total_amount, (
        f"Expected payments to sum to {total_amount}, got {payments_total}"
    )

    unconfirmed = [p for p in payments if p.status != "unconfirmed"]
    assert not unconfirmed, (
        f"Expected all installments to have status='unconfirmed', "
        f"but found: {[(p.no_installment, p.status) for p in unconfirmed]}"
    )


# ---------------------------------------------------------------------------
# Test 2: non-exact division — rounding must not lose or gain cents
# ---------------------------------------------------------------------------
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
      - DB contains exactly 3 Payment rows and their amounts sum to exactly 100.00,
        meaning the service correctly adjusts one installment to absorb the rounding remainder.
      - All installments have status="unconfirmed".
      - After manually changing installment #1 amount to 33.35, the sum of all
        installments no longer equals the original total (100.02 ≠ 100.00), which
        demonstrates that the invariant is broken when amounts are modified externally.
    """
    account_id = await _create_credit_card(client, auth_headers)
    first_payment_date = _next_month_date()
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
    assert payments_total == total_amount, (
        f"Expected payments to sum to {total_amount}, got {payments_total} "
        f"(individual amounts: {[str(p.amount) for p in payments]})"
    )

    # --- Step 2: verify all installments are unconfirmed ---
    wrong_status = [p for p in payments if p.status != "unconfirmed"]
    assert not wrong_status, (
        f"Expected all installments to have status='unconfirmed', "
        f"but found: {[(p.no_installment, p.status) for p in wrong_status]}"
    )

    # --- Step 3: change installment #1 amount via API and re-verify sum ---
    # Installments after creation (decreasing-balance): [33.33, 33.34, 33.33].
    # Setting #1 → 33.35: remaining_budget = 100.00 − 33.35 = 66.65
    # Redistributed across [#2, #3]:
    #   #2: round(66.65 / 2, 2) = 33.32 → balance: 33.33
    #   #3: round(33.33 / 1, 2) = 33.33
    # Expected final: [33.35, 33.32, 33.33] → sum = 100.00
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
    assert payments_total_after == total_amount, (
        f"Expected payments to still sum to {total_amount} after modifying installment #1 via API, "
        f"got {payments_total_after} "
        f"(individual amounts: {[str(p.amount) for p in payments_after_sorted]})"
    )

    # Verify the exact recalculated amounts.
    assert payments_after_sorted[0].amount == Decimal("33.35"), (
        f"Expected installment #1 = 33.35, got {payments_after_sorted[0].amount}"
    )
    assert payments_after_sorted[1].amount == Decimal("33.32"), (
        f"Expected installment #2 = 33.32, got {payments_after_sorted[1].amount}"
    )
    assert payments_after_sorted[2].amount == Decimal("33.33"), (
        f"Expected installment #3 = 33.33, got {payments_after_sorted[2].amount}"
    )

    # --- Step 4: confirm installment #1 ---
    # Update status to 'confirmed'
    patch_status_res = await client.patch(
        f"/api/v1/expenses/payments/{installment_1.id}",
        json={"status": "confirmed", "version_id": payments_after_sorted[0].version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert patch_status_res.status_code == 200, patch_status_res.text
    assert patch_status_res.json()["data"]["status"] == "confirmed"

    # --- Step 5: change installment #2 amount to 33.33 ---
    # Installment #1 is locked (33.35). Target for #2 is 33.33.
    # Remaining budget: 100.00 - 33.35 (locked) - 33.33 (new) = 33.32
    # Redistributed to unconfirmed (only #3): #3 gets 33.32
    # Expected final: [33.35, 33.33, 33.32] → sum = 100.00
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
    assert payments_total_final == total_amount, (
        f"Expected payments to still sum to {total_amount} after Step 5, "
        f"got {payments_total_final}"
    )

    assert payments_final_sorted[0].amount == Decimal("33.35"), "Installment #1 (locked) changed!"
    assert payments_final_sorted[1].amount == Decimal("33.33"), "Installment #2 amount not updated correctly"
    assert payments_final_sorted[2].amount == Decimal("33.32"), "Installment #3 did not absorb the remainder correctly"
    assert payments_final_sorted[0].status == "confirmed"

    # --- Step 6: lock #1 and #2 (status 'paid'), try to change #3 ---
    # Update #1 to 'paid'
    await client.patch(
        f"/api/v1/expenses/payments/{payments_final_sorted[0].id}",
        json={"status": "paid", "version_id": payments_final_sorted[0].version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    # Update #2 to 'paid'
    await client.patch(
        f"/api/v1/expenses/payments/{payments_final_sorted[1].id}",
        json={"status": "paid", "version_id": payments_final_sorted[1].version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )

    # Now #1 (33.35) and #2 (33.33) are locked. sum = 66.68.
    # #3 is unconfirmed (33.32).
    # If we try to change #3 to 10.00, remaining budget would be 23.32, but there are no unconfirmed
    # siblings left to absorb it, so it should return 422.
    db_session.expire_all()
    payments_before_step6 = sorted((await db_session.execute(stmt)).scalars().all(), key=lambda p: p.no_installment)
    patch_fail_res = await client.patch(
        f"/api/v1/expenses/payments/{payments_before_step6[2].id}",
        json={"amount": "10.00", "version_id": payments_before_step6[2].version_id},
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert patch_fail_res.status_code == 422, f"Expected 422, got {patch_fail_res.status_code}"
    error_data = patch_fail_res.json()["detail"]
    assert error_data["code"] == "PAYMENT_AMOUNT_EXCEEDS_PURCHASE_TOTAL"
    assert "No unconfirmed payments available" in error_data["message"]

