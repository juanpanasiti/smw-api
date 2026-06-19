import uuid

from src.models.account import Account, CreditCard
from src.repositories.account_repository import AccountRepository
from src.schemas.account import CreditCardCreateSchema, CreditCardUpdateSchema


class AccountService:
    def __init__(self, account_repo: AccountRepository):
        self.account_repo = account_repo

    async def get_user_accounts(self, owner_id: uuid.UUID) -> list[Account]:
        return await self.account_repo.get_all_for_owner(owner_id)

    async def create_credit_card(self, owner_id: uuid.UUID, schema: CreditCardCreateSchema) -> CreditCard:
        # If this is an extension card, validate that the parent belongs to this user
        if schema.main_credit_card_id:
            parent = await self.account_repo.get_credit_card_by_id(schema.main_credit_card_id)
            if not parent or parent.owner_id != owner_id:
                raise ValueError("PARENT_CARD_NOT_FOUND_OR_FORBIDDEN")

        credit_card = CreditCard(
            owner_id=owner_id,
            alias=schema.alias,
            is_enabled=schema.is_enabled,
            closing_day=schema.closing_day,
            due_day=schema.due_day,
            limit=schema.limit,
            financing_limit=schema.financing_limit,
            main_credit_card_id=schema.main_credit_card_id,
        )
        return await self.account_repo.create(credit_card)

    async def update_credit_card(
        self,
        owner_id: uuid.UUID,
        account_id: uuid.UUID,
        schema: CreditCardUpdateSchema,
    ) -> CreditCard:
        card = await self.account_repo.get_credit_card_by_id(account_id)
        if not card:
            raise ValueError("ACCOUNT_NOT_FOUND")
        if card.owner_id != owner_id:
            raise ValueError("FORBIDDEN_ACCOUNT")

        update_data = schema.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(card, field, value)

        return card

    async def delete_account(self, owner_id: uuid.UUID, account_id: uuid.UUID) -> None:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise ValueError("ACCOUNT_NOT_FOUND")
        if account.owner_id != owner_id:
            raise ValueError("FORBIDDEN_ACCOUNT")
        await self.account_repo.delete(account)
