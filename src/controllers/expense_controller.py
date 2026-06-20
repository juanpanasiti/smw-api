import uuid

from src.models.expense import Purchase, Subscription
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
from src.services.expense_service import ExpenseService


class ExpenseController:
    def __init__(self, expense_service: ExpenseService):
        self.expense_service = expense_service

    async def get_account_expenses(self, account_id: uuid.UUID) -> StandardResponse[list[ExpenseListItemSchema]]:
        expenses = await self.expense_service.get_account_expenses(account_id)
        data = []
        for exp in expenses:
            if isinstance(exp, Purchase):
                data.append(PurchaseResponseSchema.model_validate(exp))
            elif isinstance(exp, Subscription):
                data.append(SubscriptionResponseSchema.model_validate(exp))
        return StandardResponse(success=True, data=data)

    async def create_purchase(self, data: PurchaseCreateSchema) -> StandardResponse[PurchaseResponseSchema]:
        purchase = await self.expense_service.create_purchase(data)
        return StandardResponse(success=True, data=PurchaseResponseSchema.model_validate(purchase))

    async def create_subscription(self, data: SubscriptionCreateSchema) -> StandardResponse[SubscriptionResponseSchema]:
        subscription = await self.expense_service.create_subscription(data)
        return StandardResponse(success=True, data=SubscriptionResponseSchema.model_validate(subscription))

    async def update_payment_status(
        self, payment_id: uuid.UUID, data: PaymentUpdateSchema
    ) -> StandardResponse[PaymentResponseSchema]:
        payment = await self.expense_service.update_payment_status(payment_id, data)
        return StandardResponse(success=True, data=PaymentResponseSchema.model_validate(payment))
