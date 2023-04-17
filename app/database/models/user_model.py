import bcrypt
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import String

from . import BaseModel
from ...core.enums import RoleEnum


class UserModel(BaseModel):
    __tablename__ = 'users'

    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(60), nullable=False)
    email = Column(String(50), unique=True, index=True, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.common)

    def set_password(self, password: str):
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())
        self.password = hashed_password.decode('utf-8')

    def check_password(self, password: str):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def __repr__(self):
        return f'<User(id={self.id}, name={self.username}, email={self.email}, role={self.role})>'
