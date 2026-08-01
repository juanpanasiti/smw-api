import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.models.account import Account
from src.models.expense import Payment, Purchase, Subscription
from src.schemas.expense import SubscriptionPaymentCreateSchema
from src.services.expense_service import ExpenseService


@pytest.fixture
def mock_expense_repo():
    return AsyncMock()


@pytest.fixture
def mock_account_repo():
    return AsyncMock()


@pytest.fixture
def expense_service(mock_expense_repo, mock_account_repo):
    return ExpenseService(mock_expense_repo, mock_account_repo)


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def account_id(_: uuid.UUID) -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_account(user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    return Account(id=account_id, owner_id=user_id)


@pytest.fixture
def subscription(account_id: uuid.UUID) -> Subscription:
    return Subscription(
        id=uuid.uuid4(),
        account_id=account_id,
        title="Netflix",
        account_name="Visa",
        acquired_at=date(2026, 1, 1),
        amount=Decimal("15.00"),
        first_payment_date=date(2026, 1, 10),
    )


@pytest.fixture
def valid_payment_schema() -> SubscriptionPaymentCreateSchema:
    return SubscriptionPaymentCreateSchema(
        amount=Decimal("18.99"),
        no_installment=1,
        period_month=7,
        period_year=2026,
    )


# ---------------------------------------------------------------------------
# Test 1: expense not found → 404
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_expense_payment_expense_not_found(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    valid_payment_schema: SubscriptionPaymentCreateSchema,
    user_id: uuid.UUID,
):
    """
    Scenario: expense_id does not exist in the database.
    Input: random expense_id, valid payment schema.
    Expected: HTTPException 404 "Expense not found".
    """
    mock_expense_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.create_expense_payment(user_id, uuid.uuid4(), valid_payment_schema)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 2: expense belongs to another user → 404
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_expense_payment_wrong_owner(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    subscription: Subscription,
    valid_payment_schema: SubscriptionPaymentCreateSchema,
):
    """
    Scenario: expense exists but the account belongs to a different user.
    Input: valid expense_id for a subscription owned by another user.
    Expected: HTTPException 404 from account ownership verification.
    """
    mock_expense_repo.get_by_id.return_value = subscription
    # Return an account owned by a different user
    other_user_account = Account(id=subscription.account_id, owner_id=uuid.uuid4())
    mock_account_repo.get_by_id.return_value = other_user_account

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.create_expense_payment(uuid.uuid4(), subscription.id, valid_payment_schema)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test 3: expense is a Purchase → 400 EXPENSE_TYPE_DOES_NOT_SUPPORT_PAYMENTS
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_expense_payment_unsupported_type(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    valid_payment_schema: SubscriptionPaymentCreateSchema,
):
    """
    Scenario: expense exists and the user owns it, but the type is 'purchase'.
    Input: valid expense_id for a purchase expense.
    Expected: HTTPException 400 with error code EXPENSE_TYPE_DOES_NOT_SUPPORT_PAYMENTS.
    """
    purchase = Purchase(
        id=uuid.uuid4(),
        account_id=mock_account.id,
        title="Laptop",
        account_name="Visa",
        acquired_at=date(2026, 1, 1),
        amount=Decimal("1200.00"),
        first_payment_date=date(2026, 1, 10),
        total_installments=3,
    )
    mock_expense_repo.get_by_id.return_value = purchase
    mock_account_repo.get_by_id.return_value = mock_account

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.create_expense_payment(user_id, purchase.id, valid_payment_schema)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "EXPENSE_TYPE_DOES_NOT_SUPPORT_PAYMENTS"


# ---------------------------------------------------------------------------
# Test 4: subscription with no subsequent payment → payment created + amount updated
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_expense_payment_updates_subscription_amount(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    subscription: Subscription,
    valid_payment_schema: SubscriptionPaymentCreateSchema,
):
    """
    Scenario: subscription with no later payment than the one being created.
    Input: subscription expense, payment for 2026-07 (the most recent period).
    Expected: payment is created and subscription.amount is updated to payment.amount.
    """
    mock_expense_repo.get_by_id.return_value = subscription
    mock_account_repo.get_by_id.return_value = mock_account

    created_payment = Payment(
        id=uuid.uuid4(),
        expense_id=subscription.id,
        amount=valid_payment_schema.amount,
        no_installment=valid_payment_schema.no_installment,
        period_month=valid_payment_schema.period_month,
        period_year=valid_payment_schema.period_year,
        status=valid_payment_schema.status,
    )
    mock_expense_repo.create_payment.return_value = created_payment

    # Simulate: the just-created payment IS the latest (no subsequent payments)
    mock_expense_repo.get_latest_payment_for_expense.return_value = created_payment
    mock_expense_repo.update_expense.return_value = subscription

    result = await expense_service.create_expense_payment(user_id, subscription.id, valid_payment_schema)

    assert result.amount == valid_payment_schema.amount
    mock_expense_repo.create_payment.assert_called_once()
    mock_expense_repo.update_expense.assert_called_once()
    assert subscription.amount == valid_payment_schema.amount


# ---------------------------------------------------------------------------
# Test 5: subscription with a posterior payment → payment created but amount NOT updated
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_expense_payment_does_not_update_amount_when_posterior_exists(
    expense_service: ExpenseService,
    mock_expense_repo: AsyncMock,
    mock_account_repo: AsyncMock,
    user_id: uuid.UUID,
    mock_account: Account,
    subscription: Subscription,
):
    """
    Scenario: a payment for a future period already exists for the subscription.
    Input: new payment for 2026-05, but there is already a payment for 2026-07 in DB.
    Expected: payment is created, but subscription.amount is NOT updated.
    """
    schema = SubscriptionPaymentCreateSchema(
        amount=Decimal("14.99"),
        no_installment=5,
        period_month=5,  # older period
        period_year=2026,
    )

    mock_expense_repo.get_by_id.return_value = subscription
    mock_account_repo.get_by_id.return_value = mock_account

    created_payment = Payment(
        id=uuid.uuid4(),
        expense_id=subscription.id,
        amount=schema.amount,
        no_installment=schema.no_installment,
        period_month=schema.period_month,
        period_year=schema.period_year,
        status=schema.status,
    )
    mock_expense_repo.create_payment.return_value = created_payment

    # Simulate: there is a later payment (2026-07) already in the DB
    later_payment = Payment(
        id=uuid.uuid4(),
        expense_id=subscription.id,
        amount=Decimal("18.99"),
        no_installment=7,
        period_month=7,
        period_year=2026,
        status="unconfirmed",
    )
    mock_expense_repo.get_latest_payment_for_expense.return_value = later_payment

    original_amount = subscription.amount
    result = await expense_service.create_expense_payment(user_id, subscription.id, schema)

    assert result.amount == schema.amount
    mock_expense_repo.create_payment.assert_called_once()
    mock_expense_repo.update_expense.assert_not_called()
    assert subscription.amount == original_amount  # unchanged
