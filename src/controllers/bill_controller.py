import uuid

import structlog

from src.core.redis import invalidate_user_projections
from src.schemas.bill import (
    BillIssueCreateSchema,
    BillIssuePaySchema,
    BillIssueResponseSchema,
    BillServiceCreateSchema,
    BillServiceResponseSchema,
    BillServiceUpdateSchema,
)
from src.schemas.response import ErrorDetail, StandardResponse
from src.services.bill_service import BillServiceManager

logger = structlog.get_logger()


class BillController:
    def __init__(self, bill_service: BillServiceManager):
        self.bill_service = bill_service

    async def get_services(self, user_id: uuid.UUID) -> StandardResponse[list[BillServiceResponseSchema]]:
        services = await self.bill_service.get_services(user_id)
        data = [BillServiceResponseSchema.model_validate(s) for s in services]
        return StandardResponse(success=True, data=data)

    async def create_service(
        self, user_id: uuid.UUID, data: BillServiceCreateSchema
    ) -> StandardResponse[BillServiceResponseSchema]:
        service = await self.bill_service.create_service(user_id, data)
        return StandardResponse(success=True, data=BillServiceResponseSchema.model_validate(service))

    async def update_service(
        self, user_id: uuid.UUID, service_id: uuid.UUID, data: BillServiceUpdateSchema
    ) -> StandardResponse[BillServiceResponseSchema]:
        try:
            service = await self.bill_service.update_service(user_id, service_id, data)
            logger.info("bill_service_updated", user_id=str(user_id), service_id=str(service_id))
            return StandardResponse(success=True, data=BillServiceResponseSchema.model_validate(service))
        except ValueError as e:
            if str(e) == "BILL_SERVICE_NOT_FOUND":
                return StandardResponse(
                    success=False,
                    error=ErrorDetail(
                        code="BILL_SERVICE_NOT_FOUND",
                        message="The requested bill service does not exist or access is denied.",
                    ),
                )
            raise

    async def get_issues_by_period(
        self, user_id: uuid.UUID, period: str
    ) -> StandardResponse[list[BillIssueResponseSchema]]:
        issues = await self.bill_service.get_issues_by_period(user_id, period)
        data = [BillIssueResponseSchema.model_validate(i) for i in issues]
        return StandardResponse(success=True, data=data)

    async def create_issue(
        self, user_id: uuid.UUID, data: BillIssueCreateSchema
    ) -> StandardResponse[BillIssueResponseSchema]:
        issue = await self.bill_service.create_issue(user_id, data)
        await invalidate_user_projections(user_id)
        return StandardResponse(success=True, data=BillIssueResponseSchema.model_validate(issue))

    async def pay_issue(
        self, user_id: uuid.UUID, issue_id: uuid.UUID, data: BillIssuePaySchema
    ) -> StandardResponse[BillIssueResponseSchema]:
        issue = await self.bill_service.pay_issue(user_id, issue_id, data)
        await invalidate_user_projections(user_id)
        return StandardResponse(success=True, data=BillIssueResponseSchema.model_validate(issue))
