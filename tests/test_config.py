from pydantic_settings import SettingsConfigDict

from src.app.config import Settings


class EnvOnlySettings(Settings):
    """Settings without `.env` loading, so tests only see the process env."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    public_base_url: str = "http://localhost:5173"


def test_importable_without_any_environment(monkeypatch) -> None:
    """The old constants module crashed on import when SMTP_PORT was unset."""
    for var in ("SMTP_PORT", "SECRET_KEY", "DB_URI", "TEQUILA_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    settings = EnvOnlySettings()
    assert settings.smtp_port == 587
    assert settings.db_uri is None
    assert settings.environment == "production"


def test_reads_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("MY_UUID", "7")
    settings = EnvOnlySettings()
    assert settings.smtp_port == 465
    assert settings.environment == "dev"
    assert settings.my_uuid == 7
