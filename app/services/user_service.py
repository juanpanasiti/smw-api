from ..database.models.user_model import UserModel
from ..repositories.user_repository import UserRepository
from ..schemas.user_schemas import UserRequest
from ..schemas.user_schemas import UserResponse
from .base_service import BaseService


class UserService(BaseService[UserModel, UserRequest, UserResponse, UserRepository]):
    def __init__(self):
        super().__init__(UserRepository)

    # CRUD por defecto

    # redefinir metodos conversores
    def _to_model(self, user: UserRequest) -> UserModel:
        user_model = UserModel(**user.dict())

        if user.password:
            user_model.set_password(user.password)
        return user_model

    def _to_schema(self, user_db: UserModel) -> UserResponse:
        user = UserResponse(
            id=user_db.id,
            username=user_db.username,
            email=user_db.email,
            created_at=user_db.created_at,
            updated_at=user_db.updated_at,
        )

        return user


user_service = UserService()
