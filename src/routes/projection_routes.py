import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, status

from src.api.dependencies import get_current_user_id, get_projection_controller
from src.controllers.projection_controller import ProjectionController
from src.schemas.projection import PeriodProjectionSchema
from src.schemas.response import StandardResponse

router = APIRouter(prefix="/projections", tags=["projections"])


def _get_current_period() -> str:
    today = date.today()
    return f"{today.year}-{today.month:02d}"


@router.get(
    "/periods",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[list[PeriodProjectionSchema]],
)
async def get_multiple_projections(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ProjectionController, Depends(get_projection_controller)],
    limit: int = Query(12, ge=1, le=60, description="Número de periodos a devolver"),
    start_period: str = Query(
        default_factory=_get_current_period,
        pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$",
        description="Período inicial YYYY-MM",
    ),
) -> Any:
    return await controller.get_multiple_projections(user_id, start_period, limit)


@router.get(
    "/periods/{period}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[PeriodProjectionSchema],
)
async def get_period_projection(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[ProjectionController, Depends(get_projection_controller)],
    period: str = Path(..., pattern=r"^[0-9]{4}-(0[1-9]|1[0-2])$", description="Período YYYY-MM"),
) -> Any:
    return await controller.get_period_projection(user_id, period)
