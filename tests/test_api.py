from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.app.db import AirNomads, Base, get_engine, get_session, insert_rows
from src.app.main import app
from src.app.services import mailer
from src.app.services.tokens import issue_token
from tests.conftest import sent

PAYLOAD = {
    "username": "Timon",
    "email": "api@example.com",
    "departure_airports": ["FRA"],
    "currency": "EUR",
    "min_nights": 3,
    "max_nights": 7,
    "min_days_ahead": 10,
    "max_days_ahead": 40,
    "cadence": "weekly",
    "gem_count": 5,
    "favorite_countries": ["Finland"],
    "excluded_countries": [],
}


@pytest.fixture
def outbox(monkeypatch) -> list[tuple[str, str]]:
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        mailer,
        "send_email",
        lambda html, recipient, subject, settings: sent.append((recipient, subject)),
    )
    return sent


@pytest.fixture
def engine():
    # TestClient drives the app from another thread; sqlite must allow that.
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(engine, outbox) -> Iterator[TestClient]:
    def override() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def confirmed_at(engine):
    def lookup(email: str):
        with Session(engine) as session:
            return session.scalar(
                select(AirNomads.confirmed_at).where(AirNomads.email == email)
            )

    return lookup


def test_subscribe_creates_unconfirmed_and_sends_confirmation(client, outbox) -> None:
    response = client.post("/subscribe", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json()["confirmed"] is False
    assert outbox == [("api@example.com", "Confirm your subscription")]


def test_confirm_flow_and_409_once_confirmed(client, outbox, confirmed_at) -> None:
    subscriber_id = client.post("/subscribe", json=PAYLOAD).json()["id"]

    # resubscribing while unconfirmed resends the link instead of failing
    assert client.post("/subscribe", json=PAYLOAD).status_code == 200
    assert len(outbox) == 2

    token = issue_token(subscriber_id, "confirm")
    response = client.get(f"/confirm?token={token}")
    assert response.status_code == 200
    assert "confirmed" in response.json()["detail"]
    assert confirmed_at("api@example.com") is not None

    # confirming twice is harmless; resubscribing now conflicts
    assert client.get(f"/confirm?token={token}").status_code == 200
    assert client.post("/subscribe", json=PAYLOAD).status_code == 409


def test_confirm_rejects_other_action_tokens(client, confirmed_at) -> None:
    subscriber_id = client.post("/subscribe", json=PAYLOAD).json()["id"]
    token = issue_token(subscriber_id, "update")
    assert client.get(f"/confirm?token={token}").status_code == 401
    assert confirmed_at("api@example.com") is None


def test_put_rejects_email_change(client) -> None:
    subscriber_id = client.post("/subscribe", json=PAYLOAD).json()["id"]
    token = issue_token(subscriber_id, "update")

    changed = {**PAYLOAD, "email": "other@example.com"}
    response = client.put(f"/subscription?token={token}", json=changed)
    assert response.status_code == 400
    assert "cannot be changed" in response.json()["detail"]

    same_email = {**PAYLOAD, "username": "Renamed"}
    response = client.put(f"/subscription?token={token}", json=same_email)
    assert response.status_code == 200
    assert response.json()["username"] == "Renamed"


def test_unsubscribe_deletes(client) -> None:
    subscriber_id = client.post("/subscribe", json=PAYLOAD).json()["id"]
    token = issue_token(subscriber_id, "unsubscribe")
    assert client.get(f"/unsubscribe?token={token}").status_code == 200
    assert client.get(f"/unsubscribe?token={token}").status_code == 404


def test_deals_wall_is_public_display_ready_and_cached(sqlite_db) -> None:
    insert_rows(
        [
            sent(price=129.99, savings_percent=58, usual_price=310),
            # The same deal to a second subscriber collapses into one card.
            sent(subscriber_id=2, price=129.99, savings_percent=58, usual_price=310),
            # No baseline at send time: a card without savings or usual price.
            sent(price=80.5, arrival_iata="TKU", arrival_city="Turku"),
            # Outside the four-week window: never shown.
            sent(
                price=50,
                arrival_iata="OLD",
                sent_at=datetime.now() - timedelta(weeks=5),
            ),
        ]
    )
    # A fresh connection per thread: sqlite refuses cross-thread reuse.
    get_engine().dispose()
    with TestClient(app) as anonymous_client:
        response = anonymous_client.get("/deals")
        body = response.json()
        # Best savings first; the prices are the integers the email printed.
        assert [(d["destination"], d["price"], d["usual_price"]) for d in body] == [
            ("Helsinki", 129, 310),
            ("Turku", 80, None),
        ]
        assert body[0]["badge"] == "🔥 exceptional price"
        assert body[0]["departure_city"] == "Frankfurt"
        assert "subscriber_id" not in body[0]
        assert body[0]["image_url"].startswith("https://images.unsplash.com/")
        assert "max-age" in response.headers["Cache-Control"]


def test_subscribe_caps_favorites_at_ten(client) -> None:
    from src.app.services import refdata

    payload = {**PAYLOAD, "favorite_countries": refdata.country_choices()[:11]}
    assert client.post("/subscribe", json=payload).status_code == 422


def test_subscribe_round_trips_cadence_and_gem_count(client) -> None:
    payload = {**PAYLOAD, "cadence": "biweekly", "gem_count": 2}
    body = client.post("/subscribe", json=payload).json()
    assert body["cadence"] == "biweekly"
    assert body["gem_count"] == 2


def test_refdata_groups_countries_by_region(client) -> None:
    body = client.get("/refdata").json()
    assert "Finland" in body["regions"]["Europe"]
    assert set(body["regions"]) == {
        "Africa",
        "Asia",
        "Europe",
        "North America",
        "Oceania",
        "South America",
    }
