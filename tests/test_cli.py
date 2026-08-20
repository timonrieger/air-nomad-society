import pytest

import src.app.cli as cli
from src.app.models.subscriber import Subscriber
from tests.conftest import deal
from tests.fakes import FakeProvider


@pytest.fixture(autouse=True)
def fake_tokens(monkeypatch):
    monkeypatch.setattr(
        cli, "issue_token", lambda subscriber_id, action: f"{action}-{subscriber_id}"
    )
    monkeypatch.setattr(cli, "purge_unconfirmed", lambda: 0)


def subscriber(email: str) -> Subscriber:
    return Subscriber(
        id=1,
        username="u",
        email=email,
        departure_city="Frankfurt",
        departure_iata="FRA",
        currency="EUR",
        min_nights=2,
        max_nights=5,
        min_days_ahead=1,
        max_days_ahead=30,
        favorites=["Finland"],
        excluded=[],
        confirmed=True,
    )


def test_one_failing_subscriber_does_not_block_the_rest(monkeypatch) -> None:
    subscribers = [subscriber("fails@example.com"), subscriber("works@example.com")]
    sent: list[str] = []

    def fake_send(html: str, recipient: str, subject: str, settings) -> None:
        if recipient == "fails@example.com":
            raise RuntimeError("smtp exploded")
        sent.append(recipient)

    monkeypatch.setattr(cli, "load_subscribers", lambda only_id: subscribers)
    monkeypatch.setattr(cli.mailer, "send_email", fake_send)

    failures = cli.run_digest(FakeProvider())
    assert failures == 1
    assert sent == ["works@example.com"]


def test_all_successful_returns_zero(monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )
    monkeypatch.setattr(cli.mailer, "send_email", lambda *a, **k: None)
    assert cli.run_digest(FakeProvider()) == 0


def test_deal_fields_reach_the_email(monkeypatch) -> None:
    provider = FakeProvider({"FI": deal()})
    captured: list[tuple[str, str]] = []
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )
    monkeypatch.setattr(
        cli.mailer,
        "send_email",
        lambda html, recipient, *a, **k: captured.append((html, recipient)),
    )
    assert cli.run_digest(provider) == 0
    html, recipient = captured[0]
    assert recipient == "a@example.com"
    assert "https://kiwi.com/deep" in html
