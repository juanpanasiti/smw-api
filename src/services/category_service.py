import uuid

from src.models.category import MovementCategory
from src.repositories.category_repository import MovementCategoryRepository
from src.schemas.category import MovementCategoryCreateSchema


class MovementCategoryService:
    def __init__(self, category_repo: MovementCategoryRepository):
        self.category_repo = category_repo

    async def get_user_categories(self, user_id: uuid.UUID) -> list[MovementCategory]:
        return await self.category_repo.get_all_for_user(user_id)

    async def create_category(self, user_id: uuid.UUID, schema: MovementCategoryCreateSchema) -> MovementCategory:
        category = MovementCategory(
            user_id=user_id, name=schema.name, description=schema.description, is_income=schema.is_income
        )
        return await self.category_repo.create(category)

    async def delete_category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise ValueError("CATEGORY_NOT_FOUND")

        if category.user_id != user_id:
            raise ValueError("FORBIDDEN_GLOBAL_OR_OTHER_USER_CATEGORY")

        await self.category_repo.delete(category)
