import uuid
from datetime import date

from fastapi import HTTPException, status

from src.models.bill import BillIssue, BillService
from src.repositories.bill_repository import BillRepository
from src.schemas.bill import BillIssueCreateSchema, BillIssuePaySchema, BillServiceCreateSchema
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
