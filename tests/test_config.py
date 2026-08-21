from src.app.config import Settings


def test_digest_only_id_applies_in_dev_only(monkeypatch) -> None:
    monkeypatch.setenv("MY_UUID", "7")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    assert Settings().digest_only_id == 7  # ty: ignore[missing-argument]
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert Settings().digest_only_id is None  # ty: ignore[missing-argument]
