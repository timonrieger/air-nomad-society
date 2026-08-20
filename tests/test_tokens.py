from src.app.config import get_settings
from src.app.services.tokens import issue_token, verify_token

OTHER_SECRET = "other-secret-key-of-at-least-32-byte"  # gitleaks:allow


def test_round_trip() -> None:
    token = issue_token(42, "unsubscribe")
    assert verify_token(token, "unsubscribe") == 42


def test_action_mismatch_is_rejected() -> None:
    token = issue_token(42, "update")
    assert verify_token(token, "unsubscribe") is None


def test_tampered_token_is_rejected() -> None:
    token = issue_token(42, "update")
    assert verify_token(token[:-2] + "xx", "update") is None
    assert verify_token("garbage", "update") is None


def test_wrong_secret_is_rejected(monkeypatch) -> None:
    token = issue_token(42, "update")
    monkeypatch.setenv("SECRET_KEY", OTHER_SECRET)
    get_settings.cache_clear()
    assert verify_token(token, "update") is None
