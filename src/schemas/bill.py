import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# Bill Service Schemas
class BillServiceBase(BaseModel):
    category_id: uuid.UUID
    name: str = Field(..., max_length=100)
    service_type: str = Field(..., max_length=50)
    expected_arrival_day: int = Field(..., ge=1, le=31)
    is_active: bool = True


class BillServiceCreateSchema(BillServiceBase):
    pass


class BillServiceResponseSchema(BillServiceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Bill Issue Schemas
class BillIssueBase(BaseModel):
    period: str = Field(..., pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$")
    amount: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2, max_digits=12)
    due_date: date


class BillIssueCreateSchema(BillIssueBase):
    bill_service_id: uuid.UUID


class BillIssuePaySchema(BaseModel):
    account_id: uuid.UUID


class BillIssueResponseSchema(BillIssueBase):
    id: uuid.UUID
    bill_service_id: uuid.UUID
    status: str
    expense_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    # We can include the nested service here for convenience in lists
    bill_service: BillServiceResponseSchema | None = None

    model_config = ConfigDict(from_attributes=True)
