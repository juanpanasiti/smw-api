import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status

from src.models.account import Account
from src.models.expense import Purchase
from src.services.expense_service import ExpenseService


@pytest.mark.asyncio
async def test_delete_expense_success():
    expense_repo = AsyncMock()
    account_repo = AsyncMock()

    service = ExpenseService(
        expense_repository=expense_repo,
        account_repository=account_repo,
    )

    user_id = uuid.uuid4()
    expense_id = uuid.uuid4()
    account_id = uuid.uuid4()

    mock_expense = Purchase(id=expense_id, account_id=account_id)
    expense_repo.get_by_id.return_value = mock_expense

    mock_account = Account(id=account_id, owner_id=user_id)
    account_repo.get_by_id.return_value = mock_account

    await service.delete_expense(user_id, expense_id)

    expense_repo.get_by_id.assert_called_once_with(expense_id)
    account_repo.get_by_id.assert_called_once_with(account_id)
    expense_repo.delete.assert_called_once_with(mock_expense)


@pytest.mark.asyncio
async def test_delete_expense_not_found():
    expense_repo = AsyncMock()
    account_repo = AsyncMock()

    service = ExpenseService(
        expense_repository=expense_repo,
        account_repository=account_repo,
    )

    user_id = uuid.uuid4()
    expense_id = uuid.uuid4()

    expense_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        await service.delete_expense(user_id, expense_id)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Expense not found"
    expense_repo.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_expense_unauthorized():
    expense_repo = AsyncMock()
    account_repo = AsyncMock()

    service = ExpenseService(
        expense_repository=expense_repo,
        account_repository=account_repo,
    )

    user_id = uuid.uuid4()
    expense_id = uuid.uuid4()
    account_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    mock_expense = Purchase(id=expense_id, account_id=account_id)
    expense_repo.get_by_id.return_value = mock_expense

    mock_account = Account(id=account_id, owner_id=other_user_id)
    account_repo.get_by_id.return_value = mock_account

    with pytest.raises(HTTPException) as exc:
        await service.delete_expense(user_id, expense_id)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Account not found or access denied"
    expense_repo.delete.assert_not_called()
