from app.core import settings
from app.database import DatabaseConnection


def get_db_test() -> DatabaseConnection:
    return DatabaseConnection(settings.STR_CONN_DB_TEST)


def is_db_test_present() -> bool:
    db = get_db_test()
    if db.connect():
        db.disconnect()
        return True
    return False


skip_db_test = not is_db_test_present()
