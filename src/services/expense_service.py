import uuid

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy.orm.exc import StaleDataError

from src.models.expense import Expense, Payment, Purchase, Subscription
from src.repositories.expense_repository import ExpenseRepository
from src.schemas.expense import PaymentUpdateSchema, PurchaseCreateSchema, SubscriptionCreateSchema


class ExpenseService:
    def __init__(self, expense_repository: ExpenseRepository):
        self.expense_repository = expense_repository

    async def get_account_expenses(self, account_id: uuid.UUID) -> list[Expense]:
        return await self.expense_repository.get_all_for_account(account_id)

    async def create_purchase(self, data: PurchaseCreateSchema) -> Purchase:
        purchase = Purchase(
            account_id=data.account_id,
            category_id=data.category_id,
            title=data.title,
            account_name=data.account_name,
            acquired_at=data.acquired_at,
            amount=data.amount,
            first_payment_date=data.first_payment_date,
            description=data.description,
            total_installments=data.total_installments,
        )

        purchase = await self.expense_repository.create(purchase)

        # Calculate installments (payments)
        payments = []
        installment_amount = data.amount / data.total_installments
        for i in range(data.total_installments):
            payment_date = data.first_payment_date + relativedelta(months=i)
            is_last = i == data.total_installments - 1
            payment = Payment(
                expense_id=purchase.id,
                amount=installment_amount,
                no_installment=i + 1,
                period_month=payment_date.month,
                period_year=payment_date.year,
                status="unconfirmed",
                is_last_payment=is_last,
            )
            payments.append(payment)

        await self.expense_repository.create_payments(payments)
        return purchase

    async def create_subscription(self, data: SubscriptionCreateSchema) -> Subscription:
        subscription = Subscription(
            account_id=data.account_id,
            category_id=data.category_id,
            title=data.title,
            account_name=data.account_name,
            acquired_at=data.acquired_at,
            amount=data.amount,
            first_payment_date=data.first_payment_date,
            description=data.description,
        )
        # Note: Dynamic simulations for Subscriptions will be done in projections layer.
        # We don't generate physical payments upfront for subscriptions.
        return await self.expense_repository.create(subscription)

    async def update_payment_status(self, payment_id: uuid.UUID, data: PaymentUpdateSchema) -> Payment:
        payment = await self.expense_repository.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

        if payment.version_id != data.version_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment has been modified by another transaction. Please retry.",
            )

        payment.status = data.status
        try:
            return await self.expense_repository.update_payment(payment)
        except StaleDataError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment has been modified by another transaction. Please retry.",
            ) from e
