from unittest import TestCase

from ..utils.test_helpers import get_db_test
from app.database.models import BaseModel


class BaseTestDB(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = get_db_test()
        cls.db_connected = cls.db.connect()
        if cls.db_connected:
            BaseModel.metadata.create_all(cls.db.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.db_connected:
            BaseModel.metadata.drop_all(cls.db.engine)
