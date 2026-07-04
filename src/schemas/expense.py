import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExpenseBaseSchema(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    title: str = Field(..., max_length=255)
    account_name: str = Field(..., max_length=255)
    acquired_at: date
    amount: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2, max_digits=12)
    first_payment_date: date
    description: str | None = Field(None, max_length=1000)


class PurchaseCreateSchema(ExpenseBaseSchema):
    total_installments: int = Field(..., ge=1)


class SubscriptionCreateSchema(ExpenseBaseSchema):
    pass


class ExpenseResponseSchema(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    title: str
    account_name: str
    acquired_at: date
    amount: Decimal
    first_payment_date: date
    is_active: bool
    description: str | None
    version_id: int
    expense_type: Literal["expense"] = "expense"

    model_config = ConfigDict(from_attributes=True)


class PurchaseResponseSchema(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    title: str
    account_name: str
    acquired_at: date
    amount: Decimal
    first_payment_date: date
    is_active: bool
    description: str | None
    version_id: int
    expense_type: Literal["purchase"] = "purchase"
    total_installments: int

    model_config = ConfigDict(from_attributes=True)


class SubscriptionResponseSchema(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    title: str
    account_name: str
    acquired_at: date
    amount: Decimal
    first_payment_date: date
    is_active: bool
    description: str | None
    version_id: int
    expense_type: Literal["subscription"] = "subscription"

    model_config = ConfigDict(from_attributes=True)


ExpenseListItemSchema = Annotated[
    PurchaseResponseSchema | SubscriptionResponseSchema | ExpenseResponseSchema, Field(discriminator="expense_type")
]


class PaymentResponseSchema(BaseModel):
    id: uuid.UUID
    expense_id: uuid.UUID
    amount: Decimal
    no_installment: int
    period_month: int
    period_year: int
    status: str
    is_last_payment: bool
    credit_card_code: str | None
    version_id: int

    model_config = ConfigDict(from_attributes=True)


class SubscriptionPaymentCreateSchema(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2, max_digits=12)
    no_installment: int = Field(..., ge=1)
    period_month: int = Field(..., ge=1, le=12)
    period_year: int = Field(..., ge=2000)
    status: str = Field(default="unconfirmed")
    credit_card_code: str = Field(default="")


class PaymentUpdateSchema(BaseModel):
    """
    Schema for updating a payment. All business fields are optional,
    but at least one must be provided (enforced at the service layer).
    version_id is always required for optimistic locking.
    """

    amount: Decimal | None = Field(None, gt=Decimal("0.00"), decimal_places=2, max_digits=12)
    period_month: int | None = Field(None, ge=1, le=12)
    period_year: int | None = Field(None, ge=2000)
    status: str | None = None
    credit_card_code: str | None = None
    version_id: int  # required for optimistic locking
