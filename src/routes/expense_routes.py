import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from src.api.dependencies import get_current_user_id, get_expense_controller
from src.controllers.expense_controller import ExpenseController
from src.schemas.expense import (
    ExpenseListItemSchema,
    PaymentResponseSchema,
    PaymentUpdateSchema,
    PurchaseCreateSchema,
    PurchaseResponseSchema,
    SubscriptionCreateSchema,
    SubscriptionResponseSchema,
)
from src.schemas.response import StandardResponse

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get(
    "/account/{account_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[list[ExpenseListItemSchema]],
)
async def get_account_expenses(
    account_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ExpenseController, Depends(get_expense_controller)],
):
    return await controller.get_account_expenses(user_id, account_id)


@router.post(
    "/purchase",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[PurchaseResponseSchema],
)
async def create_purchase(
    data: PurchaseCreateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ExpenseController, Depends(get_expense_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
):
    return await controller.create_purchase(user_id, data)


@router.post(
    "/subscription",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[SubscriptionResponseSchema],
)
async def create_subscription(
    data: SubscriptionCreateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ExpenseController, Depends(get_expense_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
):
    return await controller.create_subscription(user_id, data)


@router.patch(
    "/payments/{payment_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[PaymentResponseSchema],
)
async def update_payment_status(
    payment_id: uuid.UUID,
    data: PaymentUpdateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ExpenseController, Depends(get_expense_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
):
    return await controller.update_payment_status(user_id, payment_id, data)
