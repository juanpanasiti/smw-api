import uuid

import structlog

from src.schemas.category import (
    MovementCategoryCreateSchema,
    MovementCategoryResponseSchema,
    MovementCategoryUpdateSchema,
)
from src.schemas.response import ErrorDetail, StandardResponse
from src.services.category_service import MovementCategoryService

logger = structlog.get_logger()


class MovementCategoryController:
    def __init__(self, category_service: MovementCategoryService):
        self.category_service = category_service

    async def get_all(self, user_id: uuid.UUID) -> StandardResponse[list[MovementCategoryResponseSchema]]:
        categories = await self.category_service.get_user_categories(user_id)
        data = [MovementCategoryResponseSchema.model_validate(c) for c in categories]
        return StandardResponse(success=True, data=data)

    async def create(
        self, user_id: uuid.UUID, schema: MovementCategoryCreateSchema
    ) -> StandardResponse[MovementCategoryResponseSchema]:
        category = await self.category_service.create_category(user_id, schema)
        logger.info("category_created", user_id=str(user_id), category_id=str(category.id))
        return StandardResponse(success=True, data=MovementCategoryResponseSchema.model_validate(category))

    async def update(
        self, user_id: uuid.UUID, category_id: uuid.UUID, schema: MovementCategoryUpdateSchema
    ) -> StandardResponse[MovementCategoryResponseSchema]:
        try:
            category = await self.category_service.update_category(user_id, category_id, schema)
            logger.info("category_updated", user_id=str(user_id), category_id=str(category_id))
            return StandardResponse(success=True, data=MovementCategoryResponseSchema.model_validate(category))
        except ValueError as e:
            if str(e) == "CATEGORY_NOT_FOUND":
                return StandardResponse(
                    success=False,
                    error=ErrorDetail(code="CATEGORY_NOT_FOUND", message="The requested category does not exist."),
                )
            if str(e) == "FORBIDDEN_GLOBAL_OR_OTHER_USER_CATEGORY":
                return StandardResponse(
                    success=False,
                    error=ErrorDetail(
                        code="FORBIDDEN_OPERATION",
                        message="Cannot update global categories or categories owned by other users.",
                    ),
                )
            if str(e) == "CATEGORY_HAS_EXPENSES":
                return StandardResponse(
                    success=False,
                    error=ErrorDetail(
                        code="CATEGORY_HAS_EXPENSES",
                        message="Cannot update is_income because there are expenses associated with this category.",
                    ),
                )
            raise

    async def delete(self, user_id: uuid.UUID, category_id: uuid.UUID) -> StandardResponse[None]:
        try:
            await self.category_service.delete_category(user_id, category_id)
            logger.info("category_deleted", user_id=str(user_id), category_id=str(category_id))
            return StandardResponse(success=True, data=None)
        except ValueError as e:
            if str(e) == "CATEGORY_NOT_FOUND":
                return StandardResponse(
                    success=False,
                    error=ErrorDetail(code="CATEGORY_NOT_FOUND", message="The requested category does not exist."),
                )
            if str(e) == "FORBIDDEN_GLOBAL_OR_OTHER_USER_CATEGORY":
                return StandardResponse(
                    success=False,
                    error=ErrorDetail(
                        code="FORBIDDEN_OPERATION",
                        message="Cannot delete global categories or categories owned by other users.",
                    ),
                )
            raise
