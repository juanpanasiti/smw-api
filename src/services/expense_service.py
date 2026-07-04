import uuid
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from src.models.expense import Expense, Payment, Purchase, Subscription
from src.repositories.account_repository import AccountRepository
from src.repositories.expense_repository import ExpenseRepository
from src.schemas.expense import PaymentUpdateSchema, PurchaseCreateSchema, SubscriptionCreateSchema, SubscriptionPaymentCreateSchema

# Expense types that support manual payment creation.
# Add new identifiers here when new expense types are introduced.
EXPENSE_TYPES_ALLOWING_PAYMENT_CREATION: frozenset[str] = frozenset({"subscription"})

# Payment statuses whose amounts are considered final and excluded from redistribution.
LOCKED_PAYMENT_STATUSES: frozenset[str] = frozenset({"confirmed", "paid", "cancelled"})


class ExpenseService:
    def __init__(self, expense_repository: ExpenseRepository, account_repository: AccountRepository):
        self.expense_repository = expense_repository
        self.account_repository = account_repository

    async def _verify_account_ownership(self, user_id: uuid.UUID, account_id: uuid.UUID) -> None:
        account = await self.account_repository.get_by_id(account_id)
        if not account or account.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found or access denied")

    async def get_expenses(
        self, user_id: uuid.UUID, account_id: uuid.UUID | None = None, is_active: bool | None = None
    ) -> list[Expense]:
        if account_id:
            await self._verify_account_ownership(user_id, account_id)
        return await self.expense_repository.get_filtered(user_id, account_id, is_active)

    async def create_purchase(self, user_id: uuid.UUID, data: PurchaseCreateSchema) -> Purchase:
        await self._verify_account_ownership(user_id, data.account_id)
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

        # Calculate installments using a decreasing-balance algorithm to ensure
        # the sum of all payments equals the total amount exactly, regardless of
        # rounding. Each installment = round(remaining_balance / remaining_count, 2).
        payments = []
        remaining_balance = data.amount
        for i in range(data.total_installments):
            remaining_count = data.total_installments - i
            installment_amount = round(remaining_balance / remaining_count, 2)
            remaining_balance -= installment_amount
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

    async def create_subscription(self, user_id: uuid.UUID, data: SubscriptionCreateSchema) -> Subscription:
        await self._verify_account_ownership(user_id, data.account_id)
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

    async def update_payment(
        self, user_id: uuid.UUID, payment_id: uuid.UUID, data: PaymentUpdateSchema
    ) -> Payment:
        """
        Update one or more fields of a payment.

        If `amount` is provided and differs from the stored value, the remaining
        budget is redistributed across all other unconfirmed sibling payments using
        the decreasing-balance algorithm (Purchase expenses only).

        At least one field must be provided (enforced before calling this method).
        Locked statuses for redistribution: confirmed / paid / cancelled.
        """
        payment = await self.expense_repository.get_payment_by_id(payment_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

        expense = await self.expense_repository.get_by_id(payment.expense_id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

        await self._verify_account_ownership(user_id, expense.account_id)

        if payment.version_id != data.version_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment has been modified by another transaction. Please retry.",
            )

        amount_changed = data.amount is not None and Decimal(str(data.amount)) != Decimal(str(payment.amount))

        if amount_changed:
            if not isinstance(expense, Purchase):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "EXPENSE_TYPE_DOES_NOT_SUPPORT_AMOUNT_UPDATE",
                        "message": f"Expense type '{expense.expense_type}' does not support payment amount updates.",
                        "details": {"expense_type": expense.expense_type},
                    },
                )

            all_payments = await self.expense_repository.get_payments_by_expense_id(payment.expense_id)
            new_amount = data.amount

            locked_sum: Decimal = sum(
                (Decimal(str(p.amount)) for p in all_payments if p.id != payment_id and p.status in LOCKED_PAYMENT_STATUSES),
                Decimal("0.00"),
            )

            purchase_total = Decimal(str(expense.amount))
            remaining_budget: Decimal = purchase_total - new_amount - locked_sum

            if remaining_budget < Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "PAYMENT_AMOUNT_EXCEEDS_PURCHASE_TOTAL",
                        "message": "The new amount combined with locked payments exceeds the purchase total.",
                        "details": {
                            "purchase_total": str(purchase_total),
                            "new_amount": str(new_amount),
                            "locked_sum": str(locked_sum),
                        },
                    },
                )

            redistributable = [
                p for p in all_payments
                if p.id != payment_id and p.status == "unconfirmed"
            ]

            if not redistributable and remaining_budget != Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "code": "PAYMENT_AMOUNT_EXCEEDS_PURCHASE_TOTAL",
                        "message": "No unconfirmed payments available to redistribute the remaining budget.",
                        "details": {"remaining_budget": str(remaining_budget)},
                    },
                )

            # Decreasing-balance redistribution across unconfirmed siblings.
            balance = remaining_budget
            for i, p in enumerate(redistributable):
                remaining_count = len(redistributable) - i
                p.amount = round(balance / remaining_count, 2)
                balance -= Decimal(str(p.amount))

            payment.amount = new_amount

            # Apply remaining non-amount fields.
            if data.status is not None:
                payment.status = data.status
            if data.period_month is not None:
                payment.period_month = data.period_month
            if data.period_year is not None:
                payment.period_year = data.period_year
            if data.credit_card_code is not None:
                payment.credit_card_code = data.credit_card_code

            try:
                await self.expense_repository.update_payments([payment] + redistributable)
            except StaleDataError as e:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Payment has been modified by another transaction. Please retry.",
                ) from e

            return payment

        # No amount change — apply scalar field updates directly.
        if data.status is not None:
            payment.status = data.status
        if data.period_month is not None:
            payment.period_month = data.period_month
        if data.period_year is not None:
            payment.period_year = data.period_year
        if data.credit_card_code is not None:
            payment.credit_card_code = data.credit_card_code

        try:
            return await self.expense_repository.update_payment(payment)
        except StaleDataError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment has been modified by another transaction. Please retry.",
            ) from e

    async def create_expense_payment(
        self, user_id: uuid.UUID, expense_id: uuid.UUID, data: SubscriptionPaymentCreateSchema
    ) -> Payment:
        expense = await self.expense_repository.get_by_id(expense_id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

        await self._verify_account_ownership(user_id, expense.account_id)

        if expense.expense_type not in EXPENSE_TYPES_ALLOWING_PAYMENT_CREATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "EXPENSE_TYPE_DOES_NOT_SUPPORT_PAYMENTS",
                    "message": f"Expense type '{expense.expense_type}' does not support manual payment creation.",
                    "details": {"expense_type": expense.expense_type},
                },
            )

        payment = Payment(
            expense_id=expense_id,
            amount=data.amount,
            no_installment=data.no_installment,
            period_month=data.period_month,
            period_year=data.period_year,
            status=data.status,
            credit_card_code=data.credit_card_code or None,
        )

        try:
            payment = await self.expense_repository.create_payment(payment)
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PAYMENT_PERIOD_CONFLICT",
                    "message": "A payment for this expense and period already exists.",
                    "details": {"period_month": data.period_month, "period_year": data.period_year},
                },
            ) from e

        # Update expense.amount with the new payment amount only when there is no
        # subsequent payment (i.e., the new payment is the most recent one).
        latest_payment = await self.expense_repository.get_latest_payment_for_expense(expense_id)
        new_period = (data.period_year, data.period_month)
        latest_period = (latest_payment.period_year, latest_payment.period_month) if latest_payment else new_period

        if new_period >= latest_period:
            expense.amount = data.amount
            await self.expense_repository.update_expense(expense)

        return payment

    async def delete_expense(self, user_id: uuid.UUID, expense_id: uuid.UUID) -> None:
        expense = await self.expense_repository.get_by_id(expense_id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

        await self._verify_account_ownership(user_id, expense.account_id)
        await self.expense_repository.delete(expense)


