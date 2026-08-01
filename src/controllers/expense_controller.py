import uuid

from src.core.redis import invalidate_user_projections
from src.models.expense import Purchase, Subscription
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
from src.services.expense_service import ExpenseService


class ExpenseController:
    def __init__(self, expense_service: ExpenseService):
        self.expense_service = expense_service

    async def get_expenses(
        self, user_id: uuid.UUID, account_id: uuid.UUID | None = None, is_active: bool | None = None
    ) -> StandardResponse[list[ExpenseListItemSchema]]:
        expenses = await self.expense_service.get_expenses(user_id, account_id, is_active)
        data = []
        for exp in expenses:
            if isinstance(exp, Purchase):
                data.append(PurchaseResponseSchema.model_validate(exp))
            elif isinstance(exp, Subscription):
                data.append(SubscriptionResponseSchema.model_validate(exp))
        return StandardResponse(success=True, data=data)

    async def create_purchase(
        self, user_id: uuid.UUID, data: PurchaseCreateSchema
    ) -> StandardResponse[PurchaseResponseSchema]:
        expense = await self.expense_service.create_purchase(user_id, data)
        await invalidate_user_projections(user_id)
        return StandardResponse(success=True, data=PurchaseResponseSchema.model_validate(expense))

    async def create_subscription(
        self, user_id: uuid.UUID, data: SubscriptionCreateSchema
    ) -> StandardResponse[SubscriptionResponseSchema]:
        expense = await self.expense_service.create_subscription(user_id, data)
        await invalidate_user_projections(user_id)
        return StandardResponse(success=True, data=SubscriptionResponseSchema.model_validate(expense))

    async def update_payment(
        self, user_id: uuid.UUID, payment_id: uuid.UUID, data: PaymentUpdateSchema
    ) -> StandardResponse[PaymentResponseSchema]:
        if all(
            v is None for v in (data.amount, data.period_month, data.period_year, data.status, data.credit_card_code)
        ):
            from fastapi import HTTPException
            from fastapi import status as http_status

            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "code": "NO_FIELDS_PROVIDED",
                    "message": "At least one field must be provided for update.",
                },
            )
        payment = await self.expense_service.update_payment(user_id, payment_id, data)
        await invalidate_user_projections(user_id)
        return StandardResponse(success=True, data=PaymentResponseSchema.model_validate(payment))

    async def create_expense_payment(
        self, user_id: uuid.UUID, expense_id: uuid.UUID, data: SubscriptionPaymentCreateSchema
    ) -> StandardResponse[PaymentResponseSchema]:
        payment = await self.expense_service.create_expense_payment(user_id, expense_id, data)
        await invalidate_user_projections(user_id)
        return StandardResponse(success=True, data=PaymentResponseSchema.model_validate(payment))

    async def delete_expense(self, user_id: uuid.UUID, expense_id: uuid.UUID) -> StandardResponse[None]:
        await self.expense_service.delete_expense(user_id, expense_id)
        await invalidate_user_projections(user_id)
        return StandardResponse(success=True, data=None)
