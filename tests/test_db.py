import pytest
from sqlalchemy.orm import Session

from src.config import get_settings
from src.db import AirNomads, Base, get_engine, load_subscribers


@pytest.fixture
def sqlite_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_URI", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("ENVIRONMENT", "production")  # a local .env may say dev
    get_settings.cache_clear()
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()


def member(id: int, email: str) -> AirNomads:
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
        token=f"tok-{id}",
    )


def test_round_trip_parses_subscriber(sqlite_db) -> None:
    with Session(get_engine()) as session:
        session.add(member(1, "a@example.com"))
        session.commit()

    subscribers = load_subscribers(get_settings())
    assert len(subscribers) == 1
    subscriber = subscribers[0]
    assert subscriber.favorites == ["Finland", "Japan"]
    assert subscriber.excluded == []
    assert subscriber.currency == "EUR"
    assert subscriber.min_days_ahead == 1  # server_default applied
    assert subscriber.max_days_ahead == 182


def test_dev_environment_filters_to_my_uuid(sqlite_db, monkeypatch) -> None:
    with Session(get_engine()) as session:
        session.add_all([member(1, "a@example.com"), member(2, "b@example.com")])
        session.commit()

    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("MY_UUID", "2")
    get_settings.cache_clear()
    subscribers = load_subscribers(get_settings())
    assert [s.email for s in subscribers] == ["b@example.com"]
