from datetime import date

import src.cli as cli
from src.models.subscriber import Subscriber
from src.models.flights import FlightDeal
from src.services.providers.fake import FakeProvider


def subscriber(email: str) -> Subscriber:
    return Subscriber(
        id=1,
        username="u",
        email=email,
        token="tok",
        departure_city="Frankfurt",
        departure_iata="FRA",
        currency="EUR",
        min_nights=2,
        max_nights=5,
        min_days_ahead=1,
        max_days_ahead=30,
        favorites=["Finland"],
        excluded=[],
    )


def test_one_failing_subscriber_does_not_block_the_rest(monkeypatch) -> None:
    subscribers = [subscriber("fails@example.com"), subscriber("works@example.com")]
    sent: list[str] = []

    def fake_send(html: str, recipient: str, settings) -> None:
        if recipient == "fails@example.com":
            raise RuntimeError("smtp exploded")
        sent.append(recipient)

    monkeypatch.setattr(cli, "load_subscribers", lambda settings: subscribers)
    monkeypatch.setattr(cli.mailer, "send_digest", fake_send)

    failures = cli.run_digest(FakeProvider())
    assert failures == 1
    assert sent == ["works@example.com"]


def test_all_successful_returns_zero(monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "load_subscribers", lambda settings: [subscriber("a@example.com")]
    )
    monkeypatch.setattr(cli.mailer, "send_digest", lambda *a, **k: None)
    assert cli.run_digest(FakeProvider()) == 0


def test_deal_fields_reach_the_email(monkeypatch) -> None:
    provider = FakeProvider(
        {
            "FI": FlightDeal(
                price=129.99,
                currency="EUR",
                departure_city="Frankfurt",
                departure_iata="FRA",
                arrival_city="Helsinki",
                arrival_iata="HEL",
                arrival_country="Finland",
                departs_on=date(2026, 9, 3),
                returns_on=date(2026, 9, 8),
                link="https://kiwi.com/deep",
            )
        }
    )
    captured: list[str] = []
    monkeypatch.setattr(
        cli, "load_subscribers", lambda settings: [subscriber("a@example.com")]
    )
    monkeypatch.setattr(
        cli.mailer, "send_digest", lambda html, *a, **k: captured.append(html)
    )
    assert cli.run_digest(provider) == 0
    assert ">129 EUR</strong>" in captured[0]
    assert "https://kiwi.com/deep" in captured[0]
