from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    email: str

    class Config:
        orm_mode = True


class UserRequest(UserSchema):
    password: str


class UserResponse(UserSchema):
    id: UUID
    created_at: datetime
    updated_at: datetime
