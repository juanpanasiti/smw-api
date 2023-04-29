from pydantic import BaseSettings


class Settings(BaseSettings):
    # App
    DEBUG: bool = False
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    RELOAD: bool = False

    # Database
    DB_HOST: str = ''
    DB_PORT: str = ''
    DB_USER: str = ''
    DB_PASS: str = ''
    DB_NAME: str = ''

    STR_CONN_DB: str = ''

    STR_CONN_DB_TEST: str = ''

    class Config:
        env_file = '.env'
