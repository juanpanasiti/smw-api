import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.api.dependencies import get_category_controller, get_current_user_id
from src.controllers.category_controller import MovementCategoryController
from src.schemas.category import MovementCategoryCreateSchema, MovementCategoryResponseSchema
from src.schemas.response import StandardResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=StandardResponse[list[MovementCategoryResponseSchema]])
async def get_categories(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[MovementCategoryController, Depends(get_category_controller)],
):
    return await controller.get_all(user_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=StandardResponse[MovementCategoryResponseSchema])
async def create_category(
    schema: MovementCategoryCreateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[MovementCategoryController, Depends(get_category_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
):
    return await controller.create(user_id, schema)


@router.delete("/{category_id}", status_code=status.HTTP_200_OK, response_model=StandardResponse[None])
async def delete_category(
    category_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    controller: Annotated[MovementCategoryController, Depends(get_category_controller)],
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="UUID para garantizar idempotencia"),  # noqa: ARG001
):
    response = await controller.delete(user_id, category_id)
    if not response.success:
        if response.error.code == "CATEGORY_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.model_dump())
        if response.error.code == "FORBIDDEN_OPERATION":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response.model_dump())
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.model_dump())
    return response
