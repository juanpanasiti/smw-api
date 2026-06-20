import uuid
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.account_controller import AccountController
from src.controllers.auth_controller import AuthController
from src.controllers.bill_controller import BillController
from src.controllers.category_controller import MovementCategoryController
from src.controllers.expense_controller import ExpenseController
from src.core.config import settings
from src.core.database import get_db_session
from src.core.redis import get_redis_client
from src.core.security import ALGORITHM, SECRET_KEY
from src.repositories.account_repository import AccountRepository
from src.repositories.bill_repository import BillRepository
from src.repositories.category_repository import MovementCategoryRepository
from src.repositories.expense_repository import ExpenseRepository
from src.repositories.user_repository import UserRepository
from src.services.account_service import AccountService
from src.services.auth_service import AuthService
from src.services.bill_service import BillServiceManager
from src.services.category_service import MovementCategoryService
from src.services.expense_service import ExpenseService

# Dependencia para obtener la sesión de BD
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# Dependencia para obtener el cliente de Redis
RedisClient = Annotated[aioredis.Redis, Depends(get_redis_client)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]) -> uuid.UUID:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return uuid.UUID(user_id)
    except JWTError as e:
        raise credentials_exception from e


# Auth
def get_user_repository(session: DbSession) -> UserRepository:
    return UserRepository(session)


def get_auth_service(repo: Annotated[UserRepository, Depends(get_user_repository)]) -> AuthService:
    return AuthService(repo)


def get_auth_controller(service: Annotated[AuthService, Depends(get_auth_service)]) -> AuthController:
    return AuthController(service)


# Categories
def get_category_repository(session: DbSession) -> MovementCategoryRepository:
    return MovementCategoryRepository(session)


def get_category_service(
    repo: Annotated[MovementCategoryRepository, Depends(get_category_repository)],
) -> MovementCategoryService:
    return MovementCategoryService(repo)


def get_category_controller(
    service: Annotated[MovementCategoryService, Depends(get_category_service)],
) -> MovementCategoryController:
    return MovementCategoryController(service)


# Accounts
def get_account_repository(session: DbSession) -> AccountRepository:
    return AccountRepository(session)


def get_account_service(
    repo: Annotated[AccountRepository, Depends(get_account_repository)],
) -> AccountService:
    return AccountService(repo)


def get_account_controller(
    service: Annotated[AccountService, Depends(get_account_service)],
) -> AccountController:
    return AccountController(service)


# Expenses
async def get_expense_repository(session: DbSession) -> ExpenseRepository:
    return ExpenseRepository(session=session)


async def get_expense_service(
    expense_repository: Annotated[ExpenseRepository, Depends(get_expense_repository)],
    account_repository: Annotated[AccountRepository, Depends(get_account_repository)],
) -> ExpenseService:
    return ExpenseService(expense_repository=expense_repository, account_repository=account_repository)


async def get_expense_controller(
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
) -> ExpenseController:
    return ExpenseController(expense_service=expense_service)


async def get_bill_repository(db_session: Annotated[AsyncSession, Depends(get_db_session)]) -> BillRepository:
    return BillRepository(session=db_session)


async def get_bill_service(
    bill_repository: Annotated[BillRepository, Depends(get_bill_repository)],
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
) -> BillServiceManager:
    return BillServiceManager(bill_repository=bill_repository, expense_service=expense_service)


async def get_bill_controller(
    bill_service: Annotated[BillServiceManager, Depends(get_bill_service)],
) -> BillController:
    return BillController(bill_service=bill_service)
