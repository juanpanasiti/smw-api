import structlog

from src.schemas.response import ErrorDetail, StandardResponse
from src.schemas.token import Token
from src.schemas.user import UserCreateSchema, UserLoginSchema, UserResponseSchema
from src.services.auth_service import AuthService

logger = structlog.get_logger()


class AuthController:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def register(self, schema: UserCreateSchema) -> StandardResponse[UserResponseSchema]:
        try:
            user = await self.auth_service.register_user(schema)
            logger.info("user_registered", email=user.email, user_id=str(user.id))
            return StandardResponse(success=True, data=UserResponseSchema.model_validate(user))
        except ValueError as e:
            if str(e) == "EMAIL_ALREADY_REGISTERED":
                return StandardResponse(
                    success=False,
                    error=ErrorDetail(
                        code="EMAIL_ALREADY_REGISTERED",
                        message="The provided email is already in use.",
                    ),
                )
            raise

    async def login(self, schema: UserLoginSchema) -> StandardResponse[Token]:
        try:
            token = await self.auth_service.login_user(schema)
            logger.info("user_logged_in", email=schema.email)
            return StandardResponse(success=True, data=token)
        except ValueError as e:
            if str(e) == "INVALID_CREDENTIALS":
                return StandardResponse(
                    success=False,
                    error=ErrorDetail(
                        code="INVALID_CREDENTIALS",
                        message="Incorrect email or password.",
                    ),
                )
            raise
