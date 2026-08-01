from typing import Any
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status

from src.api.dependencies import get_current_user_id, get_expense_controller
from src.api.routes_classes import IdempotentRoute
from src.controllers.expense_controller import ExpenseController
from src.schemas.expense import (
    ExpenseListItemSchema,
    PaymentResponseSchema,
    PaymentUpdateSchema,
    PurchaseCreateSchema,
    PurchaseResponseSchema,
    SubscriptionCreateSchema,
    SubscriptionPaymentCreateSchema,
    SubscriptionResponseSchema,
)
from src.schemas.response import StandardResponse

router = APIRouter(prefix="/expenses", tags=["expenses"], route_class=IdempotentRoute)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[list[ExpenseListItemSchema]],
)
async def get_expenses(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ExpenseController, Depends(get_expense_controller)],
    account_id: uuid.UUID | None = Query(None, description="Filtrar por ID de cuenta"),
    is_active: bool | None = Query(None, description="Filtrar por estado activo/inactivo (True/False)"),
) -> Any:
    return await controller.get_expenses(user_id, account_id, is_active)


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
) -> Any:
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
) -> Any:
    return await controller.create_subscription(user_id, data)


@router.post(
    "/{expense_id}/payments",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[PaymentResponseSchema],
)
async def create_expense_payment(
    expense_id: uuid.UUID,
    data: SubscriptionPaymentCreateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ExpenseController, Depends(get_expense_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
) -> Any:
    return await controller.create_expense_payment(user_id, expense_id, data)


@router.patch(
    "/payments/{payment_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[PaymentResponseSchema],
)
async def update_payment(
    payment_id: uuid.UUID,
    data: PaymentUpdateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ExpenseController, Depends(get_expense_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
) -> Any:
    return await controller.update_payment(user_id, payment_id, data)


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[None],
)
async def delete_expense(
    expense_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ExpenseController, Depends(get_expense_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
) -> Any:
    return await controller.delete_expense(user_id, expense_id)
