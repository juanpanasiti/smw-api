import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MovementCategoryCreateSchema(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=1000)
    is_income: bool = False


class MovementCategoryUpdateSchema(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=1000)
    is_income: bool | None = None

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "MovementCategoryUpdateSchema":
        if self.name is None and self.description is None and self.is_income is None:
            raise ValueError("At least one field must be provided for update")
        return self


class MovementCategoryResponseSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    description: str | None
    is_income: bool

    model_config = ConfigDict(from_attributes=True)
