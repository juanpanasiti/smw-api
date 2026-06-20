import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectin_polymorphic

from src.models.expense import Expense, Payment, Purchase, Subscription


class ExpenseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, expense: Expense) -> Expense:
        self.session.add(expense)
        await self.session.commit()
        await self.session.refresh(expense)
        return expense

    async def get_filtered(
        self, user_id: uuid.UUID, account_id: uuid.UUID | None = None, is_active: bool | None = None
    ) -> list[Expense]:
        from src.models.account import Account

        stmt = (
            select(Expense)
            .join(Account, Expense.account_id == Account.id)
            .where(Account.owner_id == user_id)
            .options(selectin_polymorphic(Expense, [Purchase, Subscription]))
            .order_by(Expense.acquired_at.desc())
        )

        if account_id:
            stmt = stmt.where(Expense.account_id == account_id)

        if is_active is not None:
            stmt = stmt.where(Expense.is_active == is_active)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, expense_id: uuid.UUID) -> Expense | None:
        stmt = (
            select(Expense)
            .where(Expense.id == expense_id)
            .options(selectin_polymorphic(Expense, [Purchase, Subscription]))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_payments(self, payments: list[Payment]) -> None:
        self.session.add_all(payments)
        await self.session.commit()

    async def get_payment_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_payment(self, payment: Payment) -> Payment:
        await self.session.commit()
        await self.session.refresh(payment)
        return payment
