import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.account import Account, CreditCard
from src.models.bill import BillIssue, BillService
from src.models.expense import Expense, Payment
from src.models.profile import Profile
from src.schemas.expense import PaymentResponseSchema
from src.schemas.projection import CreditCardUsageSchema, PeriodProjectionSchema


class ProjectionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_period_projection(self, user_id: uuid.UUID, period: str) -> PeriodProjectionSchema:
        year_str, month_str = period.split("-")
        year = int(year_str)
        month = int(month_str)

        # 1. Get User Profile for monthly limit
        stmt_profile = select(Profile).where(Profile.user_id == user_id)
        profile = (await self.session.execute(stmt_profile)).scalar_one_or_none()
        monthly_limit = profile.monthly_spending_limit if profile else Decimal("0.00")

        # 2. Get Total Expenses (Payments) for the month
        # We sum all payments that fall in this period for any account owned by the user
        stmt_expenses = (
            select(func.sum(Payment.amount))
            .join(Expense, Payment.expense_id == Expense.id)
            .join(Account, Expense.account_id == Account.id)
            .where(
                Account.owner_id == user_id,
                Payment.period_year == year,
                Payment.period_month == month,
                Payment.status != "canceled",
            )
        )
        total_expenses = (await self.session.execute(stmt_expenses)).scalar() or Decimal("0.00")

        # 2.b Get the actual payments
        stmt_payments_list = (
            select(Payment)
            .join(Expense, Payment.expense_id == Expense.id)
            .join(Account, Expense.account_id == Account.id)
            .where(
                Account.owner_id == user_id,
                Payment.period_year == year,
                Payment.period_month == month,
                Payment.status != "canceled",
            )
        )
        payments_qs = (await self.session.execute(stmt_payments_list)).scalars().all()
        payments_list = [PaymentResponseSchema.model_validate(p) for p in payments_qs]

        # 3. Get Pending Bills
        stmt_bills = (
            select(func.sum(BillIssue.amount))
            .join(BillService, BillIssue.bill_service_id == BillService.id)
            .where(
                BillService.user_id == user_id,
                BillIssue.period == period,
                BillIssue.status == "unpaid",
            )
        )
        pending_bills = (await self.session.execute(stmt_bills)).scalar() or Decimal("0.00")

        # 4. Credit Card Usage
        stmt_cards = select(CreditCard).where(CreditCard.owner_id == user_id, CreditCard.is_enabled)
        cards = (await self.session.execute(stmt_cards)).scalars().all()

        card_usages = []
        for card in cards:
            # Total debt on this card (unpaid payments)
            stmt_debt = (
                select(func.sum(Payment.amount))
                .join(Expense, Payment.expense_id == Expense.id)
                .where(
                    Expense.account_id == card.id,
                    Payment.status.in_(["unconfirmed", "confirmed"]),
                )
            )
            total_debt = (await self.session.execute(stmt_debt)).scalar() or Decimal("0.00")

            # Decimal conversion to avoid float issues
            total_debt = Decimal(total_debt).quantize(Decimal("0.00"))
            limit = Decimal(card.limit).quantize(Decimal("0.00"))
            available_limit = limit - total_debt

            card_usages.append(
                CreditCardUsageSchema(
                    account_id=str(card.id),
                    alias=card.alias,
                    total_debt=total_debt,
                    limit=limit,
                    available_limit=available_limit,
                )
            )

        total_income = monthly_limit  # Placeholder for actual income if we add Income models

        # Ensure Decimal format
        total_expenses = Decimal(total_expenses).quantize(Decimal("0.00"))
        pending_bills = Decimal(pending_bills).quantize(Decimal("0.00"))

        available_budget = total_income - total_expenses - pending_bills

        return PeriodProjectionSchema(
            period=period,
            total_income=total_income,
            total_expenses=total_expenses,
            pending_bills=pending_bills,
            available_budget=available_budget,
            credit_card_usage=card_usages,
            payments=payments_list,
        )
