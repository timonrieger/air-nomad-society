from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

import src.app.cli as cli
from src.app.db import PriceObservation, SentDeal, get_engine, insert_rows
from src.app.models.subscriber import Subscriber
from tests.conftest import deal, observation, sent
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
        departure_airports=["FRA"],
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

    failures = cli.run_digest(FakeProvider({("FRA", "FI"): [deal()]}))
    assert failures == 1
    assert sent == ["works@example.com"]


def test_all_successful_returns_zero(sqlite_db, monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )
    monkeypatch.setattr(cli.mailer, "send_email", lambda *a, **k: None)
    assert cli.run_digest(FakeProvider({("FRA", "FI"): [deal()]})) == 0


def test_empty_digest_is_not_sent(sqlite_db, monkeypatch) -> None:
    sent: list[str] = []
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )
    monkeypatch.setattr(
        cli.mailer,
        "send_email",
        lambda html, recipient, *a, **k: sent.append(recipient),
    )
    # The provider finds nothing anywhere: no email, but no failure either.
    assert cli.run_digest(FakeProvider()) == 0
    assert sent == []


def test_deal_fields_reach_the_email(sqlite_db, monkeypatch) -> None:
    provider = FakeProvider({("FRA", "FI"): [deal()]})
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


def test_price_anchor_from_earlier_runs_reaches_the_email(
    sqlite_db, monkeypatch
) -> None:
    # Observations from four earlier runs anchor FRA→HEL at a 310 median.
    month_ago = datetime.now() - timedelta(weeks=4)
    insert_rows(
        [
            observation(
                search_id="old",
                price=price,
                observed_at=month_ago + timedelta(weeks=index),
            )
            for index, price in enumerate((300, 305, 315, 320))
        ]
    )
    captured: list[str] = []
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )
    monkeypatch.setattr(
        cli.mailer, "send_email", lambda html, *a, **k: captured.append(html)
    )
    assert cli.run_digest(FakeProvider({("FRA", "FI"): [deal()]})) == 0
    assert "typically ~310 EUR (−58%)" in captured[0]
    with Session(get_engine()) as session:
        recorded = session.scalars(select(SentDeal)).one()
    # The quoted savings and the searched origin are frozen at send time.
    assert recorded.savings_percent == 58
    assert recorded.origin_iata == "FRA"
    assert recorded.arrival_city == "Helsinki"


def test_reasons_reach_the_email_and_the_history(sqlite_db, monkeypatch) -> None:
    reason = "Beat a 15 EUR cheaper option with a stop in Riga."
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )

    def fake_reasons(subscriber, digest, settings) -> None:
        digest.deals[0].reason = reason

    monkeypatch.setattr(cli, "deal_reasons", fake_reasons)
    captured: list[str] = []
    monkeypatch.setattr(
        cli.mailer, "send_email", lambda html, *a, **k: captured.append(html)
    )
    assert cli.run_digest(FakeProvider({("FRA", "FI"): [deal()]})) == 0
    assert reason in captured[0]
    with Session(get_engine()) as session:
        assert session.scalars(select(SentDeal)).one().reason == reason


def test_freshness_reads_the_sent_history_between_runs(sqlite_db, monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "load_subscribers", lambda only_id: [subscriber("a@example.com")]
    )
    captured: list[str] = []
    monkeypatch.setattr(
        cli.mailer, "send_email", lambda html, *a, **k: captured.append(html)
    )
    # Some history exists (Spain, once), but Finland was never sent — new for you.
    insert_rows([sent(arrival_country="Spain", arrival_iata="PMI")])
    assert cli.run_digest(FakeProvider({("FRA", "FI"): [deal()]})) == 0
    assert "✨ new for you" in captured[0]
    # Second run: same deal repeats at the same price — no badge, and the
    # recorded ranking score carries the repeat penalties while the quality
    # score stays what the deal is worth.
    assert cli.run_digest(FakeProvider({("FRA", "FI"): [deal()]})) == 0
    assert "✨ new for you" not in captured[1]
    with Session(get_engine()) as session:
        finland = select(SentDeal).where(SentDeal.arrival_country == "Finland")
        rows = session.scalars(finland).all()
        first, second = [row.score for row in rows]
        qualities = {row.quality_score for row in rows}
    assert second > first
    assert qualities == {first}  # run 1 was unpenalized: score == quality


def test_history_rows_written_for_candidates_and_sent_deals(
    sqlite_db, monkeypatch
) -> None:
    cheap, direct = deal(price=100, via_cities=["Riga"]), deal(price=110)
    provider = FakeProvider({("FRA", "FI"): [cheap, direct]})
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
    provider = FakeProvider({("FRA", "FI"): [deal()]})
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
