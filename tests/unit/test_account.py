import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.models.account import CreditCard
from src.schemas.account import CreditCardCreateSchema, CreditCardUpdateSchema
from src.services.account_service import AccountService


@pytest.fixture
def mock_account_repo():
    return AsyncMock()


@pytest.fixture
def account_service(mock_account_repo):
    return AccountService(mock_account_repo)


@pytest.mark.asyncio
async def test_get_user_accounts(account_service, mock_account_repo):
    owner_id = uuid.uuid4()
    mock_account_repo.get_all_for_owner.return_value = [
        CreditCard(id=uuid.uuid4(), alias="Visa Gold", owner_id=owner_id),
    ]

    accounts = await account_service.get_user_accounts(owner_id)
    assert len(accounts) == 1
    mock_account_repo.get_all_for_owner.assert_called_once_with(owner_id)


@pytest.mark.asyncio
async def test_create_credit_card(account_service, mock_account_repo):
    owner_id = uuid.uuid4()
    mock_account_repo.create.side_effect = lambda x: x

    schema = CreditCardCreateSchema(
        alias="Visa Gold",
        closing_day=10,
        due_day=20,
        limit=Decimal("5000.00"),
        financing_limit=Decimal("2500.00"),
    )

    card = await account_service.create_credit_card(owner_id, schema)
    assert card.alias == schema.alias
    assert card.owner_id == owner_id
    assert card.limit == Decimal("5000.00")
    mock_account_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_extension_card_forbidden(account_service, mock_account_repo):
    owner_id = uuid.uuid4()
    other_owner_id = uuid.uuid4()
    parent_id = uuid.uuid4()

    # Parent belongs to another user
    mock_account_repo.get_credit_card_by_id.return_value = CreditCard(
        id=parent_id, owner_id=other_owner_id, alias="Parent"
    )

    schema = CreditCardCreateSchema(
        alias="Extension",
        closing_day=10,
        due_day=20,
        limit=Decimal("1000.00"),
        financing_limit=Decimal("500.00"),
        main_credit_card_id=parent_id,
    )

    with pytest.raises(ValueError, match="PARENT_CARD_NOT_FOUND_OR_FORBIDDEN"):
        await account_service.create_credit_card(owner_id, schema)


@pytest.mark.asyncio
async def test_delete_account_forbidden(account_service, mock_account_repo):
    owner_id = uuid.uuid4()
    other_owner_id = uuid.uuid4()
    account_id = uuid.uuid4()

    mock_account_repo.get_by_id.return_value = CreditCard(id=account_id, owner_id=other_owner_id, alias="Other card")

    with pytest.raises(ValueError, match="FORBIDDEN_ACCOUNT"):
        await account_service.delete_account(owner_id, account_id)


@pytest.mark.asyncio
async def test_update_credit_card_not_found(account_service, mock_account_repo):
    owner_id = uuid.uuid4()
    mock_account_repo.get_credit_card_by_id.return_value = None

    schema = CreditCardUpdateSchema(alias="New name")

    with pytest.raises(ValueError, match="ACCOUNT_NOT_FOUND"):
        await account_service.update_credit_card(owner_id, uuid.uuid4(), schema)
