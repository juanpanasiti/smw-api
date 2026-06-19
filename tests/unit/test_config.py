import os

from src.core.config import Settings


def test_settings_load_default() -> None:
    # Aseguramos que no haya variables de entorno que interfieran
    if "POSTGRES_USER" in os.environ:
        del os.environ["POSTGRES_USER"]

    settings = Settings()
    assert settings.PROJECT_NAME == "Personal Finance API"
    assert settings.POSTGRES_USER == "postgres"
    assert settings.API_V1_STR == "/api/v1"


def test_settings_custom_env(monkeypatch) -> None:
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")

    settings = Settings()

    assert settings.POSTGRES_USER == "test_user"
    assert settings.POSTGRES_PASSWORD == "test_pass"
    assert "test_user:test_pass" in settings.async_database_url
