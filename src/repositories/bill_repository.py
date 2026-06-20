import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.bill import BillIssue, BillService


class BillRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_services_by_user(self, user_id: uuid.UUID) -> list[BillService]:
        stmt = select(BillService).where(BillService.user_id == user_id).order_by(BillService.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_service_by_id(self, service_id: uuid.UUID) -> BillService | None:
        stmt = select(BillService).where(BillService.id == service_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_service(self, service: BillService) -> BillService:
        self.session.add(service)
        await self.session.flush()
        return service

    async def update_service(self, service: BillService) -> BillService:
        await self.session.flush()
        await self.session.refresh(service)
        return service

    async def get_issues_by_service_and_period(self, service_id: uuid.UUID, period: str) -> BillIssue | None:
        stmt = select(BillIssue).where(
            BillIssue.bill_service_id == service_id,
            BillIssue.period == period,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_issues_by_user_and_period(self, user_id: uuid.UUID, period: str) -> list[BillIssue]:
        stmt = (
            select(BillIssue)
            .join(BillService, BillIssue.bill_service_id == BillService.id)
            .where(
                BillService.user_id == user_id,
                BillIssue.period == period,
            )
            .options(joinedload(BillIssue.bill_service))
            .order_by(BillIssue.due_date)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_issue_by_id(self, issue_id: uuid.UUID) -> BillIssue | None:
        stmt = select(BillIssue).where(BillIssue.id == issue_id).options(joinedload(BillIssue.bill_service))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_issue(self, issue: BillIssue) -> BillIssue:
        self.session.add(issue)
        await self.session.flush()
        await self.session.refresh(issue, attribute_names=["bill_service"])
        return issue

    async def update_issue(self, issue: BillIssue) -> BillIssue:
        await self.session.flush()
        await self.session.refresh(issue, attribute_names=["bill_service"])
        return issue
