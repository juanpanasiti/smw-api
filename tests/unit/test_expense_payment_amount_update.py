import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.models.account import Account
from src.models.expense import Payment, Purchase, Subscription
from src.schemas.expense import PaymentUpdateSchema
from src.services.expense_service import ExpenseService


@pytest.fixture
def mock_expense_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_account_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def expense_service(mock_expense_repo: AsyncMock, mock_account_repo: AsyncMock) -> ExpenseService:
    return ExpenseService(mock_expense_repo, mock_account_repo)


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def account_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_account(user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    return Account(id=account_id, owner_id=user_id)


def _make_purchase(account_id: uuid.UUID, amount: str = "100.00", installments: int = 3) -> Purchase:
    return Purchase(
        id=uuid.uuid4(),
        account_id=account_id,
        title="Test Purchase",
        account_name="Test Card",
        acquired_at=date(2026, 1, 1),
        amount=Decimal(amount),
        first_payment_date=date(2026, 2, 10),
        total_installments=installments,
    )


def _make_payment(
    expense_id: uuid.UUID,
    no_installment: int,
    amount: str,
    status: str = "unconfirmed",
    version_id: int = 1,
) -> Payment:
    return Payment(
        id=uuid.uuid4(),
        expense_id=expense_id,
        amount=Decimal(amount),
        no_installment=no_installment,
        period_month=no_installment,
        period_year=2026,
        status=status,
        version_id=version_id,
    )


# ---------------------------------------------------------------------------
# Test 1: payment not found → 404
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_payment_payment_not_found(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    user_id: uuid.UUID,
) -> None:
    """
    Scenario: The given payment_id does not exist in the database.
    Input: random payment_id; PaymentUpdateSchema with only status.
    Expected: HTTPException 404 "Payment not found".
    """
    mock_expense_repo.get_payment_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.update_payment(
            user_id,
            uuid.uuid4(),
            PaymentUpdateSchema(status="confirmed", version_id=1),
        )

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 2: account belongs to another user → 404
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_payment_wrong_owner(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    account_id: uuid.UUID,
) -> None:
    """
    Scenario: Payment exists but the account belongs to a different user.
    Input: valid payment_id; account owned by another user.
    Expected: HTTPException 404 from _verify_account_ownership.
    """
    purchase = _make_purchase(account_id)
    payment = _make_payment(purchase.id, 1, "33.33")
    mock_expense_repo.get_payment_by_id.return_value = payment
    mock_expense_repo.get_by_id.return_value = purchase
    mock_account_repo.get_by_id.return_value = Account(id=account_id, owner_id=uuid.uuid4())

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.update_payment(
            uuid.uuid4(),
            payment.id,
            PaymentUpdateSchema(status="confirmed", version_id=1),
        )

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 3: amount change on a Subscription → 400
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_payment_amount_not_allowed_for_subscription(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    account_id: uuid.UUID,
) -> None:
    """
    Scenario: The parent expense is a Subscription; user tries to change the amount.
    Input: valid payment belonging to a Subscription; data includes a different amount.
    Expected: HTTPException 400 EXPENSE_TYPE_DOES_NOT_SUPPORT_AMOUNT_UPDATE.
    """
    subscription = Subscription(
        id=uuid.uuid4(),
        account_id=account_id,
        title="Netflix",
        account_name="Visa",
        acquired_at=date(2026, 1, 1),
        amount=Decimal("15.00"),
        first_payment_date=date(2026, 2, 10),
    )
    payment = _make_payment(subscription.id, 1, "15.00")
    mock_expense_repo.get_payment_by_id.return_value = payment
    mock_expense_repo.get_by_id.return_value = subscription
    mock_account_repo.get_by_id.return_value = mock_account

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.update_payment(
            user_id,
            payment.id,
            PaymentUpdateSchema(amount=Decimal("20.00"), version_id=1),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "EXPENSE_TYPE_DOES_NOT_SUPPORT_AMOUNT_UPDATE"


# ---------------------------------------------------------------------------
# Test 4: optimistic locking mismatch → 409
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_payment_optimistic_lock_conflict(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    account_id: uuid.UUID,
) -> None:
    """
    Scenario: The version_id in the request does not match the current payment version.
    Input: payment with version_id=1; request sends version_id=999.
    Expected: HTTPException 409.
    """
    purchase = _make_purchase(account_id)
    payment = _make_payment(purchase.id, 1, "33.33", version_id=1)
    mock_expense_repo.get_payment_by_id.return_value = payment
    mock_expense_repo.get_by_id.return_value = purchase
    mock_account_repo.get_by_id.return_value = mock_account

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.update_payment(
            user_id,
            payment.id,
            PaymentUpdateSchema(status="confirmed", version_id=999),
        )

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Test 5: new amount + locked_sum exceeds purchase total → 422
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_payment_amount_exceeds_purchase_total(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    account_id: uuid.UUID,
) -> None:
    """
    Scenario: Payments #2 and #3 are 'paid' (70.00 total); user tries to set #1 → 40.00.
    Input: purchase total = 100.00; locked_sum = 70.00; new_amount = 40.00 → 110.00 > 100.00.
    Expected: HTTPException 422 PAYMENT_AMOUNT_EXCEEDS_PURCHASE_TOTAL.
    """
    purchase = _make_purchase(account_id, "100.00", 3)
    p1 = _make_payment(purchase.id, 1, "30.00", "unconfirmed", version_id=1)
    p2 = _make_payment(purchase.id, 2, "35.00", "paid")
    p3 = _make_payment(purchase.id, 3, "35.00", "paid")
    mock_expense_repo.get_payment_by_id.return_value = p1
    mock_expense_repo.get_by_id.return_value = purchase
    mock_account_repo.get_by_id.return_value = mock_account
    mock_expense_repo.get_payments_by_expense_id.return_value = [p1, p2, p3]

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.update_payment(
            user_id,
            p1.id,
            PaymentUpdateSchema(amount=Decimal("40.00"), version_id=1),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "PAYMENT_AMOUNT_EXCEEDS_PURCHASE_TOTAL"


# ---------------------------------------------------------------------------
# Test 6: happy path — exact division (1200.00 / 3), change #1 → 500.00
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_payment_amount_exact_redistribution(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    account_id: uuid.UUID,
) -> None:
    """
    Scenario: Purchase 1200.00 / 3 = [400.00, 400.00, 400.00]. Change #1 → 500.00.
    Remaining budget: 1200.00 − 500.00 = 700.00; split across [#2, #3]:
      #2: round(700.00 / 2, 2) = 350.00 → balance: 350.00
      #3: round(350.00 / 1, 2) = 350.00
    Expected: [500.00, 350.00, 350.00] → sum = 1200.00.
    """
    purchase = _make_purchase(account_id, "1200.00", 3)
    p1 = _make_payment(purchase.id, 1, "400.00", "unconfirmed", version_id=1)
    p2 = _make_payment(purchase.id, 2, "400.00", "unconfirmed")
    p3 = _make_payment(purchase.id, 3, "400.00", "unconfirmed")
    mock_expense_repo.get_payment_by_id.return_value = p1
    mock_expense_repo.get_by_id.return_value = purchase
    mock_account_repo.get_by_id.return_value = mock_account
    mock_expense_repo.get_payments_by_expense_id.return_value = [p1, p2, p3]
    mock_expense_repo.update_payments.side_effect = lambda payments: payments

    await expense_service.update_payment(
        user_id,
        p1.id,
        PaymentUpdateSchema(amount=Decimal("500.00"), version_id=1),
    )

    assert p1.amount == Decimal("500.00")
    assert p2.amount == Decimal("350.00")
    assert p3.amount == Decimal("350.00")
    assert p1.amount + p2.amount + p3.amount == Decimal("1200.00")
    mock_expense_repo.update_payments.assert_called_once()


# ---------------------------------------------------------------------------
# Test 7: happy path — non-exact (100.00 / 3), change #1 → 33.35
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_payment_amount_non_divisible_redistribution(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    account_id: uuid.UUID,
) -> None:
    """
    Scenario: Purchase 100.00 / 3 = [33.33, 33.34, 33.33]. Change #1 → 33.35.
    Remaining budget: 100.00 − 33.35 = 66.65; split across [#2, #3]:
      #2: round(66.65 / 2, 2) = 33.32 (banker's rounding) → balance: 33.33
      #3: round(33.33 / 1, 2) = 33.33
    Expected: [33.35, 33.32, 33.33] → sum = 100.00.
    """
    purchase = _make_purchase(account_id, "100.00", 3)
    p1 = _make_payment(purchase.id, 1, "33.33", "unconfirmed", version_id=1)
    p2 = _make_payment(purchase.id, 2, "33.34", "unconfirmed")
    p3 = _make_payment(purchase.id, 3, "33.33", "unconfirmed")
    mock_expense_repo.get_payment_by_id.return_value = p1
    mock_expense_repo.get_by_id.return_value = purchase
    mock_account_repo.get_by_id.return_value = mock_account
    mock_expense_repo.get_payments_by_expense_id.return_value = [p1, p2, p3]
    mock_expense_repo.update_payments.side_effect = lambda payments: payments

    await expense_service.update_payment(
        user_id,
        p1.id,
        PaymentUpdateSchema(amount=Decimal("33.35"), version_id=1),
    )

    assert p1.amount == Decimal("33.35")
    assert p2.amount == Decimal("33.32")
    assert p3.amount == Decimal("33.33")
    assert p1.amount + p2.amount + p3.amount == Decimal("100.00")
    mock_expense_repo.update_payments.assert_called_once()


# ---------------------------------------------------------------------------
# Test 8: mixed locked / unconfirmed — locked excluded from redistribution
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_payment_amount_with_locked_payments(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    account_id: uuid.UUID,
) -> None:
    """
    Scenario: Purchase 100.00 / 3. Installment #3 is 'paid' (33.33 locked).
    Change #1 → 40.00. Remaining budget: 100.00 − 40.00 − 33.33 = 26.67.
    Only #2 is unconfirmed → #2 gets 26.67.
    Expected: [40.00, 26.67, 33.33 (unchanged)] → sum = 100.00.
    """
    purchase = _make_purchase(account_id, "100.00", 3)
    p1 = _make_payment(purchase.id, 1, "33.33", "unconfirmed", version_id=1)
    p2 = _make_payment(purchase.id, 2, "33.34", "unconfirmed")
    p3 = _make_payment(purchase.id, 3, "33.33", "paid")
    mock_expense_repo.get_payment_by_id.return_value = p1
    mock_expense_repo.get_by_id.return_value = purchase
    mock_account_repo.get_by_id.return_value = mock_account
    mock_expense_repo.get_payments_by_expense_id.return_value = [p1, p2, p3]
    mock_expense_repo.update_payments.side_effect = lambda payments: payments

    await expense_service.update_payment(
        user_id,
        p1.id,
        PaymentUpdateSchema(amount=Decimal("40.00"), version_id=1),
    )

    assert p1.amount == Decimal("40.00")
    assert p2.amount == Decimal("26.67")
    assert p3.amount == Decimal("33.33")  # locked — unchanged
    assert p1.amount + p2.amount + p3.amount == Decimal("100.00")
    mock_expense_repo.update_payments.assert_called_once()


# ---------------------------------------------------------------------------
# Test 9: same amount sent → no redistribution triggered
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_payment_same_amount_no_redistribution(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    account_id: uuid.UUID,
) -> None:
    """
    Scenario: Amount in the request equals the stored amount — treated as no-change.
    Input: payment amount = 33.33; data.amount = 33.33 (same value).
    Expected: update_payment (scalar) is called, NOT update_payments (redistribution).
    """
    purchase = _make_purchase(account_id, "100.00", 3)
    p1 = _make_payment(purchase.id, 1, "33.33", "unconfirmed", version_id=1)
    mock_expense_repo.get_payment_by_id.return_value = p1
    mock_expense_repo.get_by_id.return_value = purchase
    mock_account_repo.get_by_id.return_value = mock_account
    mock_expense_repo.update_payment.return_value = p1

    await expense_service.update_payment(
        user_id,
        p1.id,
        PaymentUpdateSchema(amount=Decimal("33.33"), status="confirmed", version_id=1),
    )

    mock_expense_repo.update_payment.assert_called_once()
    mock_expense_repo.update_payments.assert_not_called()
    assert p1.status == "confirmed"
