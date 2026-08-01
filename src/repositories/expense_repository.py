import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectin_polymorphic

from src.models.expense import Expense, Payment, Purchase, Subscription


from typing import TypeVar
T = TypeVar("T", bound=Expense)

class ExpenseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, expense: T) -> T:
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

    async def create_payment(self, payment: Payment) -> Payment:
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def get_payment_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_latest_payment_for_expense(self, expense_id: uuid.UUID) -> Payment | None:
        """Return the Payment with the latest (period_year, period_month) for the given expense."""
        stmt = (
            select(Payment)
            .where(Payment.expense_id == expense_id)
            .order_by(Payment.period_year.desc(), Payment.period_month.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_payment(self, payment: Payment) -> Payment:
        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def update_expense(self, expense: T) -> T:
        await self.session.commit()
        await self.session.refresh(expense)
        return expense

    async def get_payments_by_expense_id(self, expense_id: uuid.UUID) -> list[Payment]:
        """Return all payments for an expense ordered by no_installment ascending."""
        stmt = select(Payment).where(Payment.expense_id == expense_id).order_by(Payment.no_installment)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_payments(self, payments: list[Payment]) -> list[Payment]:
        """Commit a batch of already-mutated Payment ORM objects and refresh each one."""
        await self.session.commit()
        for payment in payments:
            await self.session.refresh(payment)
        return payments

    async def delete(self, expense: Expense) -> None:
        await self.session.delete(expense)
        await self.session.commit()
