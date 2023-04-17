from fastapi import APIRouter
from fastapi import Depends

from ...exceptions.server_exceptions import InternalServerError
from app.schemas.user_schemas import UserRequest
from app.schemas.user_schemas import UserResponse
from app.services import get_user_service
from app.services import UserService

router = APIRouter(prefix='/auth')


@router.post('/register')
def register(user: UserRequest, service: UserService = Depends(get_user_service)) -> UserResponse:
    try:
        return service.create(user)
    except Exception as ex:
        # !DELETE PRINT
        print('\033[91m', ex.args, '\033[0m')
        InternalServerError('Not handled error')
