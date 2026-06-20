from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.expense import PaymentResponseSchema


class CreditCardUsageSchema(BaseModel):
    account_id: str
    alias: str
    total_debt: Decimal
    limit: Decimal
    available_limit: Decimal

    model_config = ConfigDict(from_attributes=True)


class PeriodProjectionSchema(BaseModel):
    period: str  # YYYY-MM
    total_income: Decimal
    total_expenses: Decimal
    pending_bills: Decimal
    available_budget: Decimal
    credit_card_usage: list[CreditCardUsageSchema]
    payments: list[PaymentResponseSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
