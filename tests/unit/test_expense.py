import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.models.expense import Payment
from src.schemas.expense import PaymentUpdateSchema, PurchaseCreateSchema
from src.services.expense_service import ExpenseService


@pytest.fixture
def mock_expense_repo():
    return AsyncMock()


@pytest.fixture
def expense_service(mock_expense_repo):
    return ExpenseService(mock_expense_repo)


@pytest.mark.asyncio
async def test_create_purchase(expense_service, mock_expense_repo):
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

    purchase = await expense_service.create_purchase(schema)

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
async def test_optimistic_locking_payment(expense_service, mock_expense_repo):
    payment_id = uuid.uuid4()

    payment = Payment(
        id=payment_id,
        amount=Decimal("100"),
        no_installment=1,
        period_month=7,
        period_year=2026,
        status="unconfirmed",
        version_id=1,
    )

    mock_expense_repo.get_payment_by_id.return_value = payment

    # Try to update with wrong version_id (simulate race condition)
    schema = PaymentUpdateSchema(status="paid", version_id=999)

    with pytest.raises(HTTPException) as exc_info:
        await expense_service.update_payment_status(payment_id, schema)

    assert exc_info.value.status_code == 409

    # Try to update with correct version_id
    schema.version_id = 1
    mock_expense_repo.update_payment.side_effect = lambda x: x

    updated_payment = await expense_service.update_payment_status(payment_id, schema)
    assert updated_payment.status == "paid"
    mock_expense_repo.update_payment.assert_called_once()
