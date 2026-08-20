import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

import src.app.cli as cli
from src.app.db import PriceObservation, SentDeal, get_engine
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


def test_one_failing_subscriber_does_not_block_the_rest(sqlite_db, monkeypatch) -> None:
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


def test_all_successful_returns_zero(sqlite_db, monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )
    monkeypatch.setattr(cli.mailer, "send_email", lambda *a, **k: None)
    assert cli.run_digest(FakeProvider()) == 0


def test_deal_fields_reach_the_email(sqlite_db, monkeypatch) -> None:
    provider = FakeProvider({"FI": [deal()]})
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


def test_history_rows_written_for_candidates_and_sent_deals(
    sqlite_db, monkeypatch
) -> None:
    cheap, direct = deal(price=100, via_cities=["Riga"]), deal(price=110)
    provider = FakeProvider({"FI": [cheap, direct]})
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )
    monkeypatch.setattr(cli.mailer, "send_email", lambda *a, **k: None)
    assert cli.run_digest(provider) == 0

    with Session(get_engine()) as session:
        observations = session.scalars(select(PriceObservation)).all()
        sent = session.scalars(select(SentDeal)).all()
    # Every candidate is observed; only the picked winner is a sent deal.
    assert {(o.origin_iata, o.price, o.arrival_iata) for o in observations} == {
        ("FRA", 100.0, "HEL"),
        ("FRA", 110.0, "HEL"),
    }
    assert len({o.search_id for o in observations}) == 1
    assert {o.stopovers for o in observations} == {0, 1}
    assert [(s.subscriber_id, s.price, s.source) for s in sent] == [
        (1, 110.0, "favorite")
    ]
    assert sent[0].score > 0


def test_no_sent_deals_recorded_when_email_fails(sqlite_db, monkeypatch) -> None:
    provider = FakeProvider({"FI": [deal()]})
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )

    def explode(*a, **k):
        raise RuntimeError("smtp exploded")

    monkeypatch.setattr(cli.mailer, "send_email", explode)
    assert cli.run_digest(provider) == 1

    with Session(get_engine()) as session:
        assert session.scalars(select(SentDeal)).all() == []
        # Observations are still kept: the search itself succeeded.
        assert len(session.scalars(select(PriceObservation)).all()) == 1
