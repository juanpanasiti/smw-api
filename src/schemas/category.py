import uuid

from pydantic import BaseModel, ConfigDict, Field


class MovementCategoryCreateSchema(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=1000)
    is_income: bool = False


class MovementCategoryUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=1000)
    is_income: bool | None = None


class MovementCategoryResponseSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    description: str | None
    is_income: bool

    model_config = ConfigDict(from_attributes=True)
