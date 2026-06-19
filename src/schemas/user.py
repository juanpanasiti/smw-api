import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProfileCreateSchema(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    birthdate: date
    monthly_spending_limit: Decimal = Field(..., ge=Decimal("0.00"), decimal_places=2, max_digits=12)


class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    profile: ProfileCreateSchema


class ProfileResponseSchema(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    birthdate: date
    monthly_spending_limit: Decimal

    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    profile: ProfileResponseSchema | None = None

    model_config = ConfigDict(from_attributes=True)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
