from ..core import settings
from .database_connection import DatabaseConnection

# smw_db = DatabaseConnection(
#     host=f'{settings.DB_HOST}:{settings.DB_PORT}',
#     username=settings.DB_USER,
#     password=settings.DB_PASS,
#     database=settings.DB_NAME,
# )

smw_db = DatabaseConnection(str_conn=settings.STR_CONN_DB)
