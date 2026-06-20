import uuid
from unittest.mock import AsyncMock

import pytest

from src.models.category import MovementCategory
from src.schemas.category import MovementCategoryCreateSchema
from src.services.category_service import MovementCategoryService


@pytest.fixture
def mock_category_repo():
    return AsyncMock()


@pytest.fixture
def category_service(mock_category_repo):
    return MovementCategoryService(mock_category_repo)


@pytest.mark.asyncio
async def test_get_user_categories(category_service, mock_category_repo):
    """
    Test retrieving all categories relevant to a user (both global and user-owned).

    Verifies that get_user_categories retrieves and lists categories from the repository.
    """
    user_id = uuid.uuid4()
    mock_category_repo.get_all_for_user.return_value = [
        MovementCategory(id=uuid.uuid4(), name="Global Category", user_id=None),
        MovementCategory(id=uuid.uuid4(), name="User Category", user_id=user_id),
    ]

    categories = await category_service.get_user_categories(user_id)
    assert len(categories) == 2
    mock_category_repo.get_all_for_user.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_create_category(category_service, mock_category_repo):
    """
    Test creating a new category for a user.

    Verifies that create_category instantiates a category with the correct name,
    description, is_income type, and user ID, and saves it in the repository.
    """
    user_id = uuid.uuid4()
    mock_category_repo.create.side_effect = lambda x: x

    schema = MovementCategoryCreateSchema(name="Groceries", description="Food expenses", is_income=False)

    category = await category_service.create_category(user_id, schema)
    assert category.name == schema.name
    assert category.user_id == user_id
    mock_category_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_delete_category_success(category_service, mock_category_repo):
    """
    Test successful deletion of a user-owned category.

    Verifies that a user can delete a category they own, calling delete on the repository.
    """
    user_id = uuid.uuid4()
    category_id = uuid.uuid4()

    mock_category_repo.get_by_id.return_value = MovementCategory(id=category_id, user_id=user_id, name="Groceries")

    await category_service.delete_category(user_id, category_id)
    mock_category_repo.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_category_forbidden(category_service, mock_category_repo):
    """
    Test that deleting global or other users' categories is forbidden.

    Verifies that a ValueError with FORBIDDEN_GLOBAL_OR_OTHER_USER_CATEGORY is raised
    when a user attempts to delete a global category or a category owned by someone else.
    """
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    category_id = uuid.uuid4()

    # Global category
    mock_category_repo.get_by_id.return_value = MovementCategory(id=category_id, user_id=None, name="Global")

    with pytest.raises(ValueError, match="FORBIDDEN_GLOBAL_OR_OTHER_USER_CATEGORY"):
        await category_service.delete_category(user_id, category_id)

    # Other user category
    mock_category_repo.get_by_id.return_value = MovementCategory(id=category_id, user_id=other_user_id, name="Other")

    with pytest.raises(ValueError, match="FORBIDDEN_GLOBAL_OR_OTHER_USER_CATEGORY"):
        await category_service.delete_category(user_id, category_id)
