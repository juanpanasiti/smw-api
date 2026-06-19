from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.auth_controller import AuthController
from src.core.database import get_db_session
from src.core.redis import get_redis_client
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService

# Dependencia para obtener la sesión de BD
DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# Dependencia para obtener el cliente de Redis
RedisClient = Annotated[aioredis.Redis, Depends(get_redis_client)]




def get_user_repository(session: DbSession) -> UserRepository:
    return UserRepository(session)

def get_auth_service(repo: Annotated[UserRepository, Depends(get_user_repository)]) -> AuthService:
    return AuthService(repo)

def get_auth_controller(service: Annotated[AuthService, Depends(get_auth_service)]) -> AuthController:
    return AuthController(service)
