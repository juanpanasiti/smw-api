import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.models.account import Account
from src.models.expense import Payment, Purchase
from src.schemas.expense import PaymentUpdateSchema, PurchaseCreateSchema
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


@pytest.mark.asyncio
async def test_create_purchase(expense_service, mock_expense_repo, mock_account_repo):
    """
    Test creating a new purchase expense and generating its payments.

    Verifies that create_purchase creates the main Purchase object and automatically
    calculates and stores the corresponding split installment payments in the repository.
    """
    account_id = uuid.uuid4()

    schema = PurchaseCreateSchema(
        account_id=account_id,
        title="New Laptop",
        account_name="APPLE STORE",
        acquired_at=date(2026, 6, 20),
        amount=Decimal("1200.00"),
        first_payment_date=date(2026, 7, 20),
        total_installments=3,
        description="Work laptop",
    )

    mock_expense_repo.create.side_effect = lambda x: x

    # Mock account validation
    user_id = uuid.uuid4()
    mock_account = Account(id=account_id, owner_id=user_id)
    mock_account_repo.get_by_id.return_value = mock_account

    purchase = await expense_service.create_purchase(user_id, schema)

    assert purchase.title == "New Laptop"
    assert purchase.total_installments == 3
    mock_expense_repo.create.assert_called_once()

    # Check if payments were created correctly
    mock_expense_repo.create_payments.assert_called_once()
    payments_arg = mock_expense_repo.create_payments.call_args[0][0]

    assert len(payments_arg) == 3
    assert payments_arg[0].amount == Decimal("400.00")
    assert payments_arg[0].period_month == 7
    assert payments_arg[0].period_year == 2026
    assert payments_arg[2].is_last_payment is True


@pytest.mark.asyncio
async def test_optimistic_locking_payment(expense_service, mock_expense_repo, mock_account_repo):
    """
    Test optimistic locking mechanism on payment status updates.

    Verifies that updating a payment status:
    1. Fails with a 409 HTTPException when the provided version_id does not match the record's current version_id.
    2. Succeeds when the correct version_id is provided, updating the status accordingly.
    """
    payment_id = uuid.uuid4()
    user_id = uuid.uuid4()

    payment = Payment(
        id=payment_id,
        amount=Decimal("100"),
        no_installment=1,
        period_month=7,
        period_year=2026,
        status="unconfirmed",
        version_id=1,
        expense_id=uuid.uuid4(),
    )

    # Mock account validation
    mock_account = Account(id=uuid.uuid4(), owner_id=user_id)
    mock_account_repo.get_by_id.return_value = mock_account

    # Mock expense lookup
    expense = Purchase(
        id=payment.expense_id,
        account_id=mock_account.id,
        title="Test",
        account_name="Test",
        acquired_at=date(2026, 6, 20),
        amount=Decimal("100"),
        first_payment_date=date(2026, 7, 20),
        total_installments=1,
    )
    mock_expense_repo.get_by_id.return_value = expense

    mock_expense_repo.get_payment_by_id.return_value = payment

    # Try to update with wrong version_id (simulate race condition)
    schema = PaymentUpdateSchema(status="paid", version_id=999)

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.update_payment_status(user_id, payment_id, schema)

    assert exc_info.value.status_code == 409

    # Try to update with correct version_id
    schema.version_id = 1
    mock_expense_repo.update_payment.side_effect = lambda x: x

    updated_payment = await expense_service.update_payment_status(user_id, payment_id, schema)
    assert updated_payment.status == "paid"
    mock_expense_repo.update_payment.assert_called_once()
