import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.api.dependencies import get_account_controller, get_current_user_id
from src.controllers.account_controller import AccountController
from src.schemas.account import (
    AccountResponseSchema,
    CreditCardCreateSchema,
    CreditCardResponseSchema,
    CreditCardUpdateSchema,
)
from src.schemas.response import StandardResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[list[AccountResponseSchema]],
)
async def get_accounts(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[AccountController, Depends(get_account_controller)],
):
    return await controller.get_all(user_id)


@router.post(
    "/credit-cards",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[CreditCardResponseSchema],
)
async def create_credit_card(
    schema: CreditCardCreateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[AccountController, Depends(get_account_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key"),  # noqa: ARG001
):
    response, http_status = await controller.create_credit_card(user_id, schema)
    if not response.success:
        raise HTTPException(status_code=http_status, detail=response.model_dump())
    return response


@router.patch(
    "/credit-cards/{account_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[CreditCardResponseSchema],
)
async def update_credit_card(
    account_id: uuid.UUID,
    schema: CreditCardUpdateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[AccountController, Depends(get_account_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key"),  # noqa: ARG001
):
    response, http_status = await controller.update_credit_card(user_id, account_id, schema)
    if not response.success:
        raise HTTPException(status_code=http_status, detail=response.model_dump())
    return response


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[None],
)
async def delete_account(
    account_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[AccountController, Depends(get_account_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key"),  # noqa: ARG001
):
    response, http_status = await controller.delete_account(user_id, account_id)
    if not response.success:
        raise HTTPException(status_code=http_status, detail=response.model_dump())
    return response
