from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.db import AirNomads, get_engine, load_subscribers, purge_unconfirmed


def member(
    id: int, email: str, confirmed: bool = True, created_at: datetime | None = None
) -> AirNomads:
    return AirNomads(
        id=id,
        username="Timon",
        email=email,
        departure_city="Frankfurt",
        departure_iata="FRA",
        currency="eur",
        min_nights=3,
        max_nights=7,
        travel_countries="Finland, Japan",
        excluded_countries=None,
        confirmed_at=datetime.now() if confirmed else None,
        created_at=created_at or datetime.now(),
    )


def test_round_trip_parses_subscriber(sqlite_db) -> None:
    with Session(get_engine()) as session:
        session.add(member(1, "a@example.com"))
        session.commit()

    subscribers = load_subscribers()
    assert len(subscribers) == 1
    subscriber = subscribers[0]
    assert subscriber.favorites == ["Finland", "Japan"]
    assert subscriber.min_days_ahead == 1  # server_default applied
    assert subscriber.max_days_ahead == 182


def test_only_id_filters_the_load(sqlite_db) -> None:
    with Session(get_engine()) as session:
        session.add_all([member(1, "a@example.com"), member(2, "b@example.com")])
        session.commit()

    assert [s.email for s in load_subscribers(only_id=2)] == ["b@example.com"]


def test_unconfirmed_subscribers_are_not_loaded(sqlite_db) -> None:
    with Session(get_engine()) as session:
        session.add_all(
            [member(1, "yes@example.com"), member(2, "no@example.com", confirmed=False)]
        )
        session.commit()

    assert [s.email for s in load_subscribers()] == ["yes@example.com"]


def test_purge_deletes_only_stale_unconfirmed_rows(sqlite_db) -> None:
    stale_birth = datetime.now() - timedelta(days=8)
    with Session(get_engine()) as session:
        session.add_all(
            [
                member(1, "confirmed@example.com", created_at=stale_birth),
                member(2, "fresh@example.com", confirmed=False),
                member(3, "stale@example.com", confirmed=False, created_at=stale_birth),
            ]
        )
        session.commit()

    assert purge_unconfirmed() == 1
    with Session(get_engine()) as session:
        remaining = {row.email for row in session.scalars(select(AirNomads))}
    assert remaining == {"confirmed@example.com", "fresh@example.com"}
