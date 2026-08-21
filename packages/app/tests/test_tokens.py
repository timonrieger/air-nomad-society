from src.services.tokens import issue_token, verify_token


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
