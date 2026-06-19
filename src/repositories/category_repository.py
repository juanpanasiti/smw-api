import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import MovementCategory


class MovementCategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_for_user(self, user_id: uuid.UUID) -> list[MovementCategory]:
        # Return both global categories (user_id is None) and user-specific ones
        stmt = (
            select(MovementCategory)
            .where(or_(MovementCategory.user_id == user_id, MovementCategory.user_id.is_(None)))
            .order_by(MovementCategory.name)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: uuid.UUID) -> MovementCategory | None:
        stmt = select(MovementCategory).where(MovementCategory.id == category_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, category: MovementCategory) -> MovementCategory:
        self.session.add(category)
        await self.session.flush()
        return category

    async def delete(self, category: MovementCategory) -> None:
        await self.session.delete(category)
        await self.session.flush()
