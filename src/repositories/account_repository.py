import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectin_polymorphic

from src.models.account import Account, CreditCard


class AccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_for_owner(self, owner_id: uuid.UUID) -> list[Account]:
        stmt = (
            select(Account)
            .where(Account.owner_id == owner_id)
            .options(selectin_polymorphic(Account, [CreditCard]))
            .order_by(Account.alias)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, account_id: uuid.UUID) -> Account | None:
        stmt = (
            select(Account)
            .where(Account.id == account_id)
            .options(selectin_polymorphic(Account, [CreditCard]))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_credit_card_by_id(self, account_id: uuid.UUID) -> CreditCard | None:
        stmt = select(CreditCard).where(CreditCard.id == account_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, account: Account) -> Account:
        self.session.add(account)
        await self.session.flush()
        return account

    async def delete(self, account: Account) -> None:
        await self.session.delete(account)
        await self.session.flush()
