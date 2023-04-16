from pydantic import BaseSettings, BaseConfig


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

    class Config:
        env_file = '.env'
