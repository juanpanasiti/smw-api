import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.models.bill import BillIssue, BillService
from src.services.bill_service import BillServiceManager


@pytest.fixture
def mock_bill_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_expense_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def bill_service(mock_bill_repo: AsyncMock, mock_expense_service: AsyncMock) -> BillServiceManager:
    return BillServiceManager(mock_bill_repo, mock_expense_service)


# ---------------------------------------------------------------------------
# delete_issue
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_issue_success(bill_service: BillServiceManager, mock_bill_repo: AsyncMock) -> None:
    """
    Delete an existing issue that belongs to the requesting user.

    Verifies that the repository's delete_issue method is called once and no
    exception is raised.
    """
    user_id = uuid.uuid4()
    issue_id = uuid.uuid4()

    mock_service = BillService(id=uuid.uuid4(), user_id=user_id, name="Internet")
    mock_issue = BillIssue(
        id=issue_id,
        bill_service_id=mock_service.id,
        period="2026-01",
        amount=Decimal("100.00"),
        status="unpaid",
        due_date=date(2026, 1, 15),
    )
    mock_issue.bill_service = mock_service

    mock_bill_repo.get_issue_by_id.return_value = mock_issue
    mock_bill_repo.delete_issue.return_value = None

    # Should not raise
    await bill_service.delete_issue(user_id, issue_id)

    mock_bill_repo.delete_issue.assert_called_once_with(mock_issue)


@pytest.mark.asyncio
async def test_delete_issue_not_found(bill_service: BillServiceManager, mock_bill_repo: AsyncMock) -> None:
    """
    Attempt to delete an issue that does not exist.

    Verifies that a 404 HTTPException is raised when the repository returns None.
    """
    mock_bill_repo.get_issue_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await bill_service.delete_issue(uuid.uuid4(), uuid.uuid4())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_issue_other_user(bill_service: BillServiceManager, mock_bill_repo: AsyncMock) -> None:
    """
    Attempt to delete an issue owned by a different user.

    Verifies that the ownership check returns 404 (not 403) to avoid leaking
    information about resource existence.
    """
    owner_id = uuid.uuid4()
    requesting_user_id = uuid.uuid4()

    mock_service = BillService(id=uuid.uuid4(), user_id=owner_id, name="Streaming")
    mock_issue = BillIssue(
        id=uuid.uuid4(),
        bill_service_id=mock_service.id,
        period="2026-02",
        amount=Decimal("15.00"),
        status="unpaid",
        due_date=date(2026, 2, 10),
    )
    mock_issue.bill_service = mock_service

    mock_bill_repo.get_issue_by_id.return_value = mock_issue

    with pytest.raises(HTTPException) as exc_info:
        await bill_service.delete_issue(requesting_user_id, mock_issue.id)

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# delete_service
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_service_no_issues_success(
    bill_service: BillServiceManager, mock_bill_repo: AsyncMock
) -> None:
    """
    Delete a service that has no associated issues.

    Verifies that delete_service is called and no exception is raised.
    """
    user_id = uuid.uuid4()
    service_id = uuid.uuid4()

    mock_service = BillService(id=service_id, user_id=user_id, name="Electricity")
    mock_bill_repo.get_service_by_id.return_value = mock_service
    mock_bill_repo.get_issues_by_service.return_value = []
    mock_bill_repo.delete_service.return_value = None

    await bill_service.delete_service(user_id, service_id)

    mock_bill_repo.delete_service.assert_called_once_with(mock_service)


@pytest.mark.asyncio
async def test_delete_service_with_issues_no_force(
    bill_service: BillServiceManager, mock_bill_repo: AsyncMock
) -> None:
    """
    Attempt to delete a service that has issues without force=True.

    Verifies that ValueError('BILL_SERVICE_HAS_ISSUES') is raised and the
    repository delete_service is never called.
    """
    user_id = uuid.uuid4()
    service_id = uuid.uuid4()

    mock_service = BillService(id=service_id, user_id=user_id, name="Water")
    mock_bill_repo.get_service_by_id.return_value = mock_service
    mock_bill_repo.get_issues_by_service.return_value = [
        BillIssue(id=uuid.uuid4(), bill_service_id=service_id, period="2026-03", amount=Decimal("50.00"))
    ]

    with pytest.raises(ValueError, match="BILL_SERVICE_HAS_ISSUES"):
        await bill_service.delete_service(user_id, service_id, force=False)

    mock_bill_repo.delete_service.assert_not_called()


@pytest.mark.asyncio
async def test_delete_service_with_issues_force(
    bill_service: BillServiceManager, mock_bill_repo: AsyncMock
) -> None:
    """
    Delete a service with issues using force=True.

    Verifies that delete_service is called regardless of linked issues, relying
    on the ORM cascade to clean up child rows.
    """
    user_id = uuid.uuid4()
    service_id = uuid.uuid4()

    mock_service = BillService(id=service_id, user_id=user_id, name="Gas")
    mock_bill_repo.get_service_by_id.return_value = mock_service
    mock_bill_repo.delete_service.return_value = None

    await bill_service.delete_service(user_id, service_id, force=True)

    # get_issues_by_service must NOT be called when force=True (skip the guard)
    mock_bill_repo.get_issues_by_service.assert_not_called()
    mock_bill_repo.delete_service.assert_called_once_with(mock_service)


@pytest.mark.asyncio
async def test_delete_service_not_found(
    bill_service: BillServiceManager, mock_bill_repo: AsyncMock
) -> None:
    """
    Attempt to delete a service that does not exist.

    Verifies that ValueError('BILL_SERVICE_NOT_FOUND') is raised and nothing
    is deleted.
    """
    mock_bill_repo.get_service_by_id.return_value = None

    with pytest.raises(ValueError, match="BILL_SERVICE_NOT_FOUND"):
        await bill_service.delete_service(uuid.uuid4(), uuid.uuid4())

    mock_bill_repo.delete_service.assert_not_called()
