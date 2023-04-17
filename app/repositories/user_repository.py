import logging

from ..database.models import UserModel
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[UserModel]):
    def __init__(self) -> None:
        super().__init__()
        self.model = UserModel
