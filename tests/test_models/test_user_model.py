from unittest import skipIf
from uuid import UUID

from sqlalchemy.exc import DataError
from sqlalchemy.exc import IntegrityError

from ..base.base_test_db import BaseTestDB
from ..utils.test_helpers import skip_db_test
from app.database.models.user_model import UserModel


class TestUserModel(BaseTestDB):

    def setUp(self) -> None:
        self.db_session = self.db.session
        self.db_session.commit()

        self.user_1 = {
            'username': 'test_user_1',
            'password': 'test_password',
            'email': 'test_user_1@smw.com',
            'role': 'common',
        }
        self.user_2 = {
            'username': 'test_user_2',
            'password': 'test_password',
            'email': 'test_user_2@smw.com',
            'role': 'common',
        }

    def tearDown(self) -> None:
        self.db_session.query(UserModel).delete()
        self.db_session.close()

    @skipIf(skip_db_test, 'There are no test db present')
    def test_create_user(self):

        user = UserModel(**self.user_1)
        self.db_session.add(user)
        self.db_session.commit()

        self.assertIsNotNone(user.id, 'must have a value')
        self.assertIsInstance(user.id, UUID, 'must be a UserModel')
        self.assertIsInstance(user, UserModel, 'must be a UserModel')
        self.assertEqual(user.username, self.user_1['username'])
        self.assertEqual(user.password, self.user_1['password'])
        self.assertEqual(user.email, self.user_1['email'])
        self.assertEqual(user.role, self.user_1['role'])

    @skipIf(skip_db_test, 'There are no test db present')
    def test_unique_email(self):
        user_1 = UserModel(**self.user_1)
        self.db_session.add(user_1)
        self.db_session.commit()

        user_2 = UserModel(**self.user_2)
        user_2.email = user_1.email  # Set the same email
        self.db_session.add(user_2)
        with self.assertRaises(IntegrityError):
            self.db_session.commit()

    @skipIf(skip_db_test, 'There are no test db present')
    def test_unique_username(self):
        user_1 = UserModel(**self.user_1)
        self.db_session.add(user_1)
        self.db_session.commit()

        user_2 = UserModel(**self.user_2)
        user_2.username = user_1.username  # Set the same username
        self.db_session.add(user_2)
        with self.assertRaises(IntegrityError):
            self.db_session.commit()

    @skipIf(skip_db_test, 'There are no test db present')
    def test_empty_username(self):
        user = UserModel(**self.user_1)
        with self.assertRaises(Exception):
            user.username = ''

    @skipIf(skip_db_test, 'There are no test db present')
    def test_empty_password(self):
        user = UserModel(**self.user_1)
        with self.assertRaises(Exception):
            user.password = ''

    @skipIf(skip_db_test, 'There are no test db present')
    def test_empty_email(self):
        with self.assertRaises(Exception):
            UserModel(**self.user_1, email='')

    @skipIf(skip_db_test, 'There are no test db present')
    def test_empty_role(self):
        user = UserModel(**self.user_1)
        user.role = ''
        self.db_session.add(user)
        with self.assertRaises(DataError):
            self.db_session.commit()

    @skipIf(skip_db_test, 'There are no test db present')
    def test_invalid_role(self):
        user = UserModel(**self.user_1)
        user.role = 'some_weird'
        self.db_session.add(user)
        with self.assertRaises(DataError):
            self.db_session.commit()

    @skipIf(skip_db_test, 'There are no test db present')
    def test_invalid_email(self):
        user = UserModel(**self.user_1)
        with self.assertRaises(Exception):
            user.email = 'invalid_email'
        with self.assertRaises(Exception):
            user.email = 'invalid_email@'
        with self.assertRaises(Exception):
            user.email = 'invalid_email@some'
        with self.assertRaises(Exception):
            user.email = 'invalid_email@.com'
