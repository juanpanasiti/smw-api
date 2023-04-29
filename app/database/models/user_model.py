import bcrypt
from pydantic import EmailStr
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import String
from sqlalchemy.orm import validates

from . import BaseModel
from ...core.enums import RoleEnum


class UserModel(BaseModel):
    __tablename__ = 'users'

    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(60), nullable=False)
    email = Column(String(50), unique=True, index=True, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.common)

    @validates('email')
    def validate_email(self, key, email):
        assert EmailStr.validate(email), 'Not a valid email address'
        return email

    @validates('username')
    def validate_username(self, key, username):
        assert len(
            username) >= 8, f'The {key} must be greater or equal than 8 characters'
        return username

    @validates('password')
    def validate_password(self, key, password):
        assert len(
            password) >= 8, f'The {key} must be greater or equal than 8 characters'
        return password

    def set_password(self, password: str):
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())
        self.password = hashed_password.decode('utf-8')

    def check_password(self, password: str):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def __repr__(self):
        return f'<User(id={self.id}, name={self.username}, email={self.email}, role={self.role})>'
