from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.dependencies import get_auth_controller
from src.controllers.auth_controller import AuthController
from src.schemas.response import StandardResponse
from src.schemas.token import Token
from src.schemas.user import UserCreateSchema, UserLoginSchema, UserResponseSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=StandardResponse[UserResponseSchema])
async def register(
    schema: UserCreateSchema,
    controller: Annotated[AuthController, Depends(get_auth_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
):
    response = await controller.register(schema)
    if not response.success:
        # Standardize HTTP status based on business logic errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.model_dump())
    return response


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=Token
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    controller: Annotated[AuthController, Depends(get_auth_controller)]
):
    schema = UserLoginSchema(email=form_data.username, password=form_data.password)
    response = await controller.login(schema)
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=response.model_dump()
        )
    return response.data
