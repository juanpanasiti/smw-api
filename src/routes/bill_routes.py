import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status

from src.api.dependencies import get_bill_controller, get_current_user_id
from src.controllers.bill_controller import BillController
from src.schemas.bill import (
    BillIssueCreateSchema,
    BillIssuePaySchema,
    BillIssueResponseSchema,
    BillServiceCreateSchema,
    BillServiceResponseSchema,
)
from src.schemas.response import StandardResponse

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get(
    "/services",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[list[BillServiceResponseSchema]],
)
async def get_services(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[BillController, Depends(get_bill_controller)],
):
    return await controller.get_services(user_id)


@router.post(
    "/services",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[BillServiceResponseSchema],
)
async def create_service(
    data: BillServiceCreateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[BillController, Depends(get_bill_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
):
    return await controller.create_service(user_id, data)


@router.get(
    "/issues",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[list[BillIssueResponseSchema]],
)
async def get_issues_by_period(
    period: str = Query(..., pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$", description="Período YYYY-MM"),
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)] = ...,
    controller: Annotated[BillController, Depends(get_bill_controller)] = ...,
):
    return await controller.get_issues_by_period(user_id, period)


@router.post(
    "/issues",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[BillIssueResponseSchema],
)
async def create_issue(
    data: BillIssueCreateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[BillController, Depends(get_bill_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
):
    return await controller.create_issue(user_id, data)


@router.post(
    "/issues/{issue_id}/pay",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[BillIssueResponseSchema],
)
async def pay_issue(
    issue_id: uuid.UUID,
    data: BillIssuePaySchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[BillController, Depends(get_bill_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
):
    return await controller.pay_issue(user_id, issue_id, data)
