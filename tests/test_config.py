import pytest
from pydantic import ValidationError

from src.app.config import Settings


def test_defaults_apply(monkeypatch) -> None:
    monkeypatch.delenv("SMTP_PORT", raising=False)
    settings = Settings()  # ty: ignore[missing-argument]
    assert settings.smtp_port == 587
    assert settings.environment == "production"


def test_missing_required_field_fails_at_startup(monkeypatch) -> None:
    monkeypatch.delenv("SECRET_KEY")
    with pytest.raises(ValidationError):
        Settings()  # ty: ignore[missing-argument]


def test_reads_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("MY_UUID", "7")
    settings = Settings()  # ty: ignore[missing-argument]
    assert settings.smtp_port == 465
    assert settings.digest_only_id == 7


def test_digest_only_id_is_none_outside_dev(monkeypatch) -> None:
    monkeypatch.setenv("MY_UUID", "7")
    settings = Settings()  # ty: ignore[missing-argument]
    assert settings.digest_only_id is None
