from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.dependencies import get_auth_controller
from src.controllers.auth_controller import AuthController
from src.schemas.response import StandardResponse
from src.schemas.token import RefreshTokenRequest, Token
from src.schemas.user import UserCreateSchema, UserLoginSchema, UserResponseSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=StandardResponse[UserResponseSchema])
async def register(
    schema: UserCreateSchema,
    controller: Annotated[AuthController, Depends(get_auth_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
) -> Any:
    response = await controller.register(schema)
    if not response.success:
        # Standardize HTTP status based on business logic errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.model_dump())
    return response


@router.post("/login", status_code=status.HTTP_200_OK, response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    controller: Annotated[AuthController, Depends(get_auth_controller)],
) -> Any:
    schema = UserLoginSchema(email=form_data.username, password=form_data.password)
    response = await controller.login(schema)
    if not response.success:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=response.model_dump())
    return response.data


@router.post("/refresh", status_code=status.HTTP_200_OK, response_model=Token)
async def refresh(
    schema: RefreshTokenRequest,
    controller: Annotated[AuthController, Depends(get_auth_controller)],
) -> Any:
    response = await controller.refresh_tokens(schema)
    if not response.success:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=response.model_dump())
    return response.data
