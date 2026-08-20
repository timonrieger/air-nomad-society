from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import src.app.routers.subscriptions as subscriptions
from src.app.config import get_settings
from src.app.db import AirNomads, Base, get_session
from src.app.main import app
from src.app.services.tokens import issue_token

TEST_SECRET = "test-secret-key-of-at-least-32-bytes!"  # gitleaks:allow

PAYLOAD = {
    "username": "Timon",
    "email": "api@example.com",
    "departure_iata": "FRA",
    "currency": "EUR",
    "min_nights": 3,
    "max_nights": 7,
    "min_days_ahead": 10,
    "max_days_ahead": 40,
    "favorite_countries": ["Finland"],
    "excluded_countries": [],
}


@pytest.fixture
def outbox(monkeypatch) -> list[tuple[str, str]]:
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        subscriptions.mailer,
        "send_email",
        lambda html, recipient, subject, settings: sent.append((recipient, subject)),
    )
    return sent


@pytest.fixture
def client(monkeypatch, outbox) -> Iterator[TestClient]:
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)
    get_settings.cache_clear()
    # TestClient drives the app from another thread; sqlite must allow that.
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)

    def override() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override
    with TestClient(app) as client:
        client.engine = engine  # type: ignore[attr-defined]
        yield client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def confirmed_at(client: TestClient, email: str):
    with Session(client.engine) as session:  # type: ignore[attr-defined]
        return session.scalar(
            select(AirNomads.confirmed_at).where(AirNomads.email == email)
        )


def test_subscribe_creates_unconfirmed_and_sends_confirmation(client, outbox) -> None:
    response = client.post("/subscribe", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json()["confirmed"] is False
    assert outbox == [("api@example.com", "Confirm your subscription")]


def test_confirm_flow_and_409_once_confirmed(client, outbox) -> None:
    subscriber_id = client.post("/subscribe", json=PAYLOAD).json()["id"]

    # resubscribing while unconfirmed resends the link instead of failing
    assert client.post("/subscribe", json=PAYLOAD).status_code == 200
    assert len(outbox) == 2

    token = issue_token(subscriber_id, "confirm")
    response = client.get(f"/confirm?token={token}")
    assert response.status_code == 200
    assert "confirmed" in response.json()["detail"]
    assert confirmed_at(client, "api@example.com") is not None

    # confirming twice is harmless; resubscribing now conflicts
    assert client.get(f"/confirm?token={token}").status_code == 200
    assert client.post("/subscribe", json=PAYLOAD).status_code == 409


def test_confirm_rejects_other_action_tokens(client, outbox) -> None:
    subscriber_id = client.post("/subscribe", json=PAYLOAD).json()["id"]
    token = issue_token(subscriber_id, "update")
    assert client.get(f"/confirm?token={token}").status_code == 401
    assert confirmed_at(client, "api@example.com") is None


def test_put_rejects_email_change(client, outbox) -> None:
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


def test_unsubscribe_deletes(client, outbox) -> None:
    subscriber_id = client.post("/subscribe", json=PAYLOAD).json()["id"]
    token = issue_token(subscriber_id, "unsubscribe")
    assert client.get(f"/unsubscribe?token={token}").status_code == 200
    assert client.get(f"/unsubscribe?token={token}").status_code == 404
