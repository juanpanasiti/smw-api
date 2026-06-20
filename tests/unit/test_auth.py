import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.core.security import get_password_hash
from src.models.user import User
from src.schemas.user import ProfileCreateSchema, UserCreateSchema, UserLoginSchema
from src.services.auth_service import AuthService


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def auth_service(mock_user_repo):
    return AuthService(mock_user_repo)


@pytest.mark.asyncio
async def test_register_user_success(auth_service, mock_user_repo):
    """
    Test successful user registration.

    Verifies that a user is successfully registered and their profile is created
    when the email is not already registered.
    """
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.create.side_effect = lambda x: x

    schema = UserCreateSchema(
        email="test@example.com",
        password="strongpassword",
        profile=ProfileCreateSchema(
            first_name="John", last_name="Doe", birthdate=date(1990, 1, 1), monthly_spending_limit=Decimal("1000.00")
        ),
    )

    user = await auth_service.register_user(schema)
    assert user.email == schema.email
    assert user.profile.first_name == "John"
    mock_user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_existing_email(auth_service, mock_user_repo):
    """
    Test registration failure when email already exists.

    Verifies that a ValueError with EMAIL_ALREADY_REGISTERED is raised when
    attempting to register a user with an already registered email.
    """
    mock_user_repo.get_by_email.return_value = User()

    schema = UserCreateSchema(
        email="test@example.com",
        password="strongpassword",
        profile=ProfileCreateSchema(
            first_name="John", last_name="Doe", birthdate=date(1990, 1, 1), monthly_spending_limit=Decimal("1000.00")
        ),
    )

    with pytest.raises(ValueError, match="EMAIL_ALREADY_REGISTERED"):
        await auth_service.register_user(schema)


@pytest.mark.asyncio
async def test_login_user_success(auth_service, mock_user_repo):
    """
    Test successful user login.

    Verifies that a user with correct credentials receives an access token
    and a refresh token upon successful authentication.
    """
    hashed_pwd = get_password_hash("strongpassword")
    user = User(id=uuid.uuid4(), email="test@example.com", password_hash=hashed_pwd)
    mock_user_repo.get_by_email.return_value = user

    schema = UserLoginSchema(email="test@example.com", password="strongpassword")
    token = await auth_service.login_user(schema)

    assert token.access_token is not None
    assert token.refresh_token is not None


@pytest.mark.asyncio
async def test_login_user_invalid_password(auth_service, mock_user_repo):
    """
    Test login failure due to invalid password.

    Verifies that a ValueError with INVALID_CREDENTIALS is raised when the
    provided password does not match the hashed password in the database.
    """
    hashed_pwd = get_password_hash("strongpassword")
    user = User(id=uuid.uuid4(), email="test@example.com", password_hash=hashed_pwd)
    mock_user_repo.get_by_email.return_value = user

    schema = UserLoginSchema(email="test@example.com", password="wrongpassword")

    with pytest.raises(ValueError, match="INVALID_CREDENTIALS"):
        await auth_service.login_user(schema)
