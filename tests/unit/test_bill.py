import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.models.bill import BillIssue, BillService
from src.schemas.bill import BillIssueCreateSchema, BillIssuePaySchema, BillServiceCreateSchema
from src.schemas.expense import PurchaseCreateSchema
from src.services.bill_service import BillServiceManager


@pytest.fixture
def mock_bill_repo():
    return AsyncMock()


@pytest.fixture
def mock_expense_service():
    return AsyncMock()


@pytest.fixture
def bill_service(mock_bill_repo, mock_expense_service):
    return BillServiceManager(mock_bill_repo, mock_expense_service)


@pytest.mark.asyncio
async def test_create_service(bill_service, mock_bill_repo):
    user_id = uuid.uuid4()
    schema = BillServiceCreateSchema(
        category_id=uuid.uuid4(),
        name="Internet",
        service_type="internet",
        expected_arrival_day=15,
        is_active=True,
    )

    mock_bill_repo.create_service.side_effect = lambda x: x
    service = await bill_service.create_service(user_id, schema)

    assert service.name == "Internet"
    assert service.user_id == user_id
    mock_bill_repo.create_service.assert_called_once()


@pytest.mark.asyncio
async def test_create_issue_duplicate_period(bill_service, mock_bill_repo):
    user_id = uuid.uuid4()
    service_id = uuid.uuid4()

    mock_service = BillService(id=service_id, user_id=user_id, name="Internet")
    mock_bill_repo.get_service_by_id.return_value = mock_service

    # Simulate an existing issue
    mock_bill_repo.get_issues_by_service_and_period.return_value = BillIssue(id=uuid.uuid4())

    schema = BillIssueCreateSchema(
        bill_service_id=service_id,
        period="2026-06",
        amount=Decimal("50.00"),
        due_date=date(2026, 6, 20),
    )

    with pytest.raises(HTTPException) as exc_info:
        await bill_service.create_issue(user_id, schema)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_pay_issue_success(bill_service, mock_bill_repo, mock_expense_service):
    user_id = uuid.uuid4()
    issue_id = uuid.uuid4()
    account_id = uuid.uuid4()
    category_id = uuid.uuid4()

    mock_service = BillService(id=uuid.uuid4(), user_id=user_id, name="Internet", category_id=category_id)
    mock_issue = BillIssue(
        id=issue_id,
        bill_service_id=mock_service.id,
        period="2026-06",
        amount=Decimal("50.00"),
        status="unpaid",
    )
    mock_issue.bill_service = mock_service
    mock_bill_repo.get_issue_by_id.return_value = mock_issue

    # Mock expense creation
    class MockPurchase:
        id = uuid.uuid4()

    mock_expense_service.create_purchase.return_value = MockPurchase()
    mock_bill_repo.update_issue.side_effect = lambda x: x

    schema = BillIssuePaySchema(account_id=account_id)
    updated_issue = await bill_service.pay_issue(user_id, issue_id, schema)

    assert updated_issue.status == "paid"
    assert updated_issue.expense_id == MockPurchase.id

    # Check that create_purchase was called with correct data
    mock_expense_service.create_purchase.assert_called_once()
    called_args = mock_expense_service.create_purchase.call_args[0]
    assert called_args[0] == user_id
    assert isinstance(called_args[1], PurchaseCreateSchema)
    assert called_args[1].amount == Decimal("50.00")
    assert called_args[1].total_installments == 1
    assert called_args[1].account_id == account_id
    assert called_args[1].category_id == category_id
