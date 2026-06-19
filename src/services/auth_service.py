from src.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from src.models.profile import Profile
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.token import Token
from src.schemas.user import UserCreateSchema, UserLoginSchema


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, schema: UserCreateSchema) -> User:
        existing_user = await self.user_repo.get_by_email(schema.email)
        if existing_user:
            raise ValueError("EMAIL_ALREADY_REGISTERED")

        hashed_password = get_password_hash(schema.password)

        user = User(
            email=schema.email,
            password_hash=hashed_password,
            role="user"
        )

        profile = Profile(
            first_name=schema.profile.first_name,
            last_name=schema.profile.last_name,
            birthdate=schema.profile.birthdate,
            monthly_spending_limit=schema.profile.monthly_spending_limit
        )

        user.profile = profile
        return await self.user_repo.create(user)

    async def login_user(self, schema: UserLoginSchema) -> Token:
        user = await self.user_repo.get_by_email(schema.email)
        if not user:
            raise ValueError("INVALID_CREDENTIALS")

        if not verify_password(schema.password, user.password_hash):
            raise ValueError("INVALID_CREDENTIALS")

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        return Token(access_token=access_token, refresh_token=refresh_token)
