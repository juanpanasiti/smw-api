from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


# --- Base Account ---
class AccountBaseSchema(BaseModel):
    alias: str = Field(..., max_length=100)
    is_enabled: bool = True


class AccountResponseSchema(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    alias: str
    is_enabled: bool
    account_type: Literal["account"] = "account"

    model_config = ConfigDict(from_attributes=True)


# --- Credit Card ---
class CreditCardCreateSchema(AccountBaseSchema):
    closing_day: int = Field(..., ge=1, le=31)
    due_day: int = Field(..., ge=1, le=31)
    limit: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2, max_digits=12)
    financing_limit: Decimal = Field(..., ge=Decimal("0.00"), decimal_places=2, max_digits=12)
    main_credit_card_id: uuid.UUID | None = None


class CreditCardUpdateSchema(BaseModel):
    alias: str | None = Field(None, max_length=100)
    is_enabled: bool | None = None
    closing_day: int | None = Field(None, ge=1, le=31)
    due_day: int | None = Field(None, ge=1, le=31)
    limit: Decimal | None = Field(None, gt=Decimal("0.00"), decimal_places=2, max_digits=12)
    financing_limit: Decimal | None = Field(None, ge=Decimal("0.00"), decimal_places=2, max_digits=12)


class CreditCardResponseSchema(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    alias: str
    is_enabled: bool
    account_type: Literal["credit_card"] = "credit_card"
    closing_day: int
    due_day: int
    limit: Decimal
    financing_limit: Decimal
    main_credit_card_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)


# Discriminated union for polymorphic list serialization
AccountListItemSchema = Annotated[CreditCardResponseSchema | AccountResponseSchema, Field(discriminator="account_type")]
