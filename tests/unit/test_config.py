import os

from src.core.config import Settings


def test_settings_load_default() -> None:
    """
    Test that settings load default values correctly.

    Verifies that the default environment values are correctly assigned
    when no specific environment variables are set.
    """
    # Aseguramos que no haya variables de entorno que interfieran
    if "POSTGRES_USER" in os.environ:
        del os.environ["POSTGRES_USER"]

    settings = Settings()
    assert settings.PROJECT_NAME == "Personal Finance API"
    assert settings.POSTGRES_USER == "postgres"
    assert settings.API_V1_STR == "/api/v1"


def test_settings_custom_env(monkeypatch) -> None:
    """
    Test that settings respect and parse custom environment variables.

    Verifies that user-supplied environment variables (like POSTGRES_USER and POSTGRES_PASSWORD)
    are successfully picked up by the Settings class, updating the database URL accordingly.
    """
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")

    settings = Settings()

    assert settings.POSTGRES_USER == "test_user"
    assert settings.POSTGRES_PASSWORD == "test_pass"
    assert "test_user:test_pass" in settings.async_database_url
