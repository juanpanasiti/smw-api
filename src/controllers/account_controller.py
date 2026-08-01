import uuid

import structlog

from src.core.redis import invalidate_user_projections
from src.models.account import CreditCard
from src.schemas.account import (
    AccountListItemSchema,
    AccountResponseSchema,
    CreditCardCreateSchema,
    CreditCardResponseSchema,
    CreditCardUpdateSchema,
)
from src.schemas.response import ErrorDetail, StandardResponse
from src.services.account_service import AccountService

logger = structlog.get_logger()

_ERROR_MAP = {
    "ACCOUNT_NOT_FOUND": (404, "The requested account does not exist."),
    "FORBIDDEN_ACCOUNT": (403, "You do not have access to this account."),
    "PARENT_CARD_NOT_FOUND_OR_FORBIDDEN": (400, "Parent credit card not found or access denied."),
}


def _make_error_response(code: str) -> StandardResponse:
    http_status, message = _ERROR_MAP.get(code, (400, "An error occurred."))
    return StandardResponse(success=False, error=ErrorDetail(code=code, message=message)), http_status


class AccountController:
    def __init__(self, account_service: AccountService):
        self.account_service = account_service

    async def get_all(self, owner_id: uuid.UUID) -> StandardResponse[list[AccountListItemSchema]]:
        accounts = await self.account_service.get_user_accounts(owner_id)
        data: list[AccountListItemSchema] = []
        for acc in accounts:
            if isinstance(acc, CreditCard):
                data.append(CreditCardResponseSchema.model_validate(acc))
            else:
                data.append(AccountResponseSchema.model_validate(acc))
        return StandardResponse(success=True, data=data)

    async def get_account(
        self, owner_id: uuid.UUID, account_id: uuid.UUID
    ) -> tuple[StandardResponse[AccountListItemSchema], int]:
        try:
            account = await self.account_service.get_account(owner_id, account_id)
            if isinstance(account, CreditCard):
                data = CreditCardResponseSchema.model_validate(account)
            else:
                data = AccountResponseSchema.model_validate(account)
            return StandardResponse(success=True, data=data), 200
        except ValueError as e:
            return _make_error_response(str(e))

    async def create_credit_card(
        self, owner_id: uuid.UUID, schema: CreditCardCreateSchema
    ) -> tuple[StandardResponse[CreditCardResponseSchema], int]:
        try:
            card = await self.account_service.create_credit_card(owner_id, schema)
            await invalidate_user_projections(owner_id)
            logger.info("credit_card_created", owner_id=str(owner_id), card_id=str(card.id))
            return StandardResponse(success=True, data=CreditCardResponseSchema.model_validate(card)), 201
        except ValueError as e:
            return _make_error_response(str(e))

    async def update_credit_card(
        self,
        owner_id: uuid.UUID,
        account_id: uuid.UUID,
        schema: CreditCardUpdateSchema,
    ) -> tuple[StandardResponse[CreditCardResponseSchema], int]:
        try:
            card = await self.account_service.update_credit_card(owner_id, account_id, schema)
            await invalidate_user_projections(owner_id)
            logger.info("credit_card_updated", owner_id=str(owner_id), card_id=str(card.id))
            return StandardResponse(success=True, data=CreditCardResponseSchema.model_validate(card)), 200
        except ValueError as e:
            return _make_error_response(str(e))

    async def delete_account(self, owner_id: uuid.UUID, account_id: uuid.UUID) -> tuple[StandardResponse[None], int]:
        try:
            await self.account_service.delete_account(owner_id, account_id)
            await invalidate_user_projections(owner_id)
            logger.info("account_deleted", owner_id=str(owner_id), account_id=str(account_id))
            return StandardResponse(success=True, data=None), 200
        except ValueError as e:
            return _make_error_response(str(e))
