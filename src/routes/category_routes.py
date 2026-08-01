import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.api.dependencies import get_category_controller, get_current_user_id
from src.api.routes_classes import IdempotentRoute
from src.controllers.category_controller import MovementCategoryController
from src.schemas.category import (
    MovementCategoryCreateSchema,
    MovementCategoryResponseSchema,
    MovementCategoryUpdateSchema,
)
from src.schemas.response import StandardResponse

router = APIRouter(prefix="/categories", tags=["categories"], route_class=IdempotentRoute)


@router.get("/", status_code=status.HTTP_200_OK, response_model=StandardResponse[list[MovementCategoryResponseSchema]])
async def get_categories(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[MovementCategoryController, Depends(get_category_controller)],
) -> Any:
    return await controller.get_all(user_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=StandardResponse[MovementCategoryResponseSchema])
async def create_category(
    schema: MovementCategoryCreateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[MovementCategoryController, Depends(get_category_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
) -> Any:
    return await controller.create(user_id, schema)


@router.patch(
    "/{category_id}", status_code=status.HTTP_200_OK, response_model=StandardResponse[MovementCategoryResponseSchema]
)
async def update_category(
    category_id: uuid.UUID,
    schema: MovementCategoryUpdateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[MovementCategoryController, Depends(get_category_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
) -> Any:
    response = await controller.update(user_id, category_id, schema)
    if not response.success:
        if response.error and response.error.code == "CATEGORY_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.model_dump())
        if response.error and response.error.code == "FORBIDDEN_OPERATION":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response.model_dump())
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.model_dump())
    return response


@router.delete("/{category_id}", status_code=status.HTTP_200_OK, response_model=StandardResponse[None])
async def delete_category(
    category_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[MovementCategoryController, Depends(get_category_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
) -> Any:
    response = await controller.delete(user_id, category_id)
    if not response.success:
        if response.error and response.error.code == "CATEGORY_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.model_dump())
        if response.error and response.error.code == "FORBIDDEN_OPERATION":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response.model_dump())
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.model_dump())
    return response
