import uuid
from datetime import date

from fastapi import HTTPException, status

from src.models.bill import BillIssue, BillService
from src.repositories.bill_repository import BillRepository
from src.schemas.bill import (
    BillIssueCreateSchema,
    BillIssuePaySchema,
    BillIssueUpdateSchema,
    BillServiceCreateSchema,
    BillServiceUpdateSchema,
)
from src.schemas.expense import PurchaseCreateSchema
from src.services.expense_service import ExpenseService


class BillServiceManager:
    def __init__(self, bill_repository: BillRepository, expense_service: ExpenseService):
        self.bill_repository = bill_repository
        self.expense_service = expense_service

    async def get_services(self, user_id: uuid.UUID) -> list[BillService]:
        return await self.bill_repository.get_services_by_user(user_id)

    async def create_service(self, user_id: uuid.UUID, data: BillServiceCreateSchema) -> BillService:
        service = BillService(
            user_id=user_id,
            category_id=data.category_id,
            name=data.name,
            service_type=data.service_type,
            expected_arrival_day=data.expected_arrival_day,
            is_active=data.is_active,
        )
        return await self.bill_repository.create_service(service)

    async def update_service(
        self, user_id: uuid.UUID, service_id: uuid.UUID, data: BillServiceUpdateSchema
    ) -> BillService:
        service = await self.bill_repository.get_service_by_id(service_id)
        if not service or service.user_id != user_id:
            raise ValueError("BILL_SERVICE_NOT_FOUND")

        if data.category_id is not None:
            service.category_id = data.category_id
        if data.name is not None:
            service.name = data.name
        if data.service_type is not None:
            service.service_type = data.service_type
        if data.expected_arrival_day is not None:
            service.expected_arrival_day = data.expected_arrival_day
        if data.is_active is not None:
            service.is_active = data.is_active

        # NOTE: If bill service updates ever affect period projections (e.g. filtering
        # issues by is_active), invalidate_user_projections(user_id) should be called
        # here after persisting the change.
        return await self.bill_repository.update_service(service)

    async def get_issues_by_period(self, user_id: uuid.UUID, period: str) -> list[BillIssue]:
        return await self.bill_repository.get_issues_by_user_and_period(user_id, period)

    async def create_issue(self, user_id: uuid.UUID, data: BillIssueCreateSchema) -> BillIssue:
        # Verify service belongs to user
        service = await self.bill_repository.get_service_by_id(data.bill_service_id)
        if not service or service.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill service not found or access denied")

        # Verify no duplicate issue for this period
        existing_issue = await self.bill_repository.get_issues_by_service_and_period(data.bill_service_id, data.period)
        if existing_issue:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An issue for service {service.name} in period {data.period} already exists.",
            )

        issue = BillIssue(
            bill_service_id=data.bill_service_id,
            period=data.period,
            amount=data.amount,
            due_date=data.due_date,
            status="unpaid",
        )
        return await self.bill_repository.create_issue(issue)

    async def update_issue(self, user_id: uuid.UUID, issue_id: uuid.UUID, data: BillIssueUpdateSchema) -> BillIssue:
        issue = await self.bill_repository.get_issue_by_id(issue_id)
        if not issue or issue.bill_service.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill issue not found or access denied")

        if issue.status == "paid":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "BILL_ISSUE_ALREADY_PAID", "message": "A paid bill issue cannot be modified."},
            )

        if data.period is not None and data.period != issue.period:
            conflicting = await self.bill_repository.get_issue_by_service_and_period_excluding(
                issue.bill_service_id, data.period, issue.id
            )
            if conflicting:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "BILL_ISSUE_PERIOD_CONFLICT",
                        "message": f"An issue for period {data.period} already exists for this service.",
                    },
                )

        if data.amount is not None:
            issue.amount = data.amount
        if data.due_date is not None:
            issue.due_date = data.due_date
        if data.period is not None:
            issue.period = data.period
        if data.status is not None:
            issue.status = data.status

        return await self.bill_repository.update_issue(issue)

    async def pay_issue(self, user_id: uuid.UUID, issue_id: uuid.UUID, data: BillIssuePaySchema) -> BillIssue:
        issue = await self.bill_repository.get_issue_by_id(issue_id)
        if not issue or issue.bill_service.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill issue not found or access denied")

        if issue.status == "paid":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bill issue is already paid")

        # Delegate expense creation to ExpenseService. This implicitly verifies account ownership.
        purchase_data = PurchaseCreateSchema(
            account_id=data.account_id,
            category_id=issue.bill_service.category_id,
            title=f"Payment: {issue.bill_service.name} ({issue.period})",
            account_name="Bill Payment",
            acquired_at=date.today(),
            amount=issue.amount,
            first_payment_date=date.today(),
            total_installments=1,
            description=f"Automated payment for {issue.bill_service.name} bill issue {issue.period}.",
        )

        purchase = await self.expense_service.create_purchase(user_id, purchase_data)

        # Link expense and update status
        issue.expense_id = purchase.id
        issue.status = "paid"

        return await self.bill_repository.update_issue(issue)

    async def delete_issue(self, user_id: uuid.UUID, issue_id: uuid.UUID) -> None:
        """Delete a bill issue, verifying ownership before removal."""
        issue = await self.bill_repository.get_issue_by_id(issue_id)
        if not issue or issue.bill_service.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill issue not found or access denied")

        await self.bill_repository.delete_issue(issue)

    async def delete_service(self, user_id: uuid.UUID, service_id: uuid.UUID, *, force: bool = False) -> None:
        """Delete a bill service, verifying ownership before removal.

        If the service has associated issues and ``force`` is ``False``, a
        ``ValueError`` is raised so the caller can return an appropriate error
        response without deleting anything.

        When ``force`` is ``True``, the service and all its issues are deleted
        atomically: the 'cascade=all, delete-orphan' relationship on
        ``BillService.issues`` guarantees that child rows are removed within the
        same flush.  If the flush fails for any reason, the enclosing transaction
        is rolled back automatically by the session lifecycle, leaving both the
        service and its issues intact.
        """
        service = await self.bill_repository.get_service_by_id(service_id)
        if not service or service.user_id != user_id:
            raise ValueError("BILL_SERVICE_NOT_FOUND")

        if not force:
            linked_issues = await self.bill_repository.get_issues_by_service(service_id)
            if linked_issues:
                raise ValueError("BILL_SERVICE_HAS_ISSUES")

        await self.bill_repository.delete_service(service)
