import os
from datetime import datetime

import pytest

from src.app.config import Settings, get_settings
from src.app.db import Base, PriceObservation, SentDeal, get_engine
from src.app.models.flights import FlightDeal
from src.app.services.history import OBSERVED_FIELDS, SENT_FIELDS
from src.app.services.selection import deal_score

TEST_SECRET = "test-secret-key-of-at-least-32-bytes!"  # gitleaks:allow

# Tests never talk to the AI endpoint, whatever the developer's shell exports.
for var in ("AI_API_KEY", "AI_BASE_URL", "AI_MODEL"):
    os.environ.pop(var, None)

# Every Settings field is required; tests never talk to real infra.
for var, value in {
    "PUBLIC_BASE_URL": "http://localhost:5173",
    "SECRET_KEY": TEST_SECRET,
    "DB_URI": "sqlite://",
    "TEQUILA_API_KEY": "test-tequila-key",
    "SMTP_EMAIL": "digest@example.com",
    "SMTP_PWD": "test-smtp-pwd",
    "SMTP_SERVER": "smtp.example.com",
}.items():
    os.environ.setdefault(var, value)


@pytest.fixture
def sqlite_db(tmp_path, monkeypatch):
    """A file-backed sqlite database with the full schema created."""
    monkeypatch.setenv("DB_URI", f"sqlite:///{tmp_path}/test.db")
    get_settings.cache_clear()
    get_engine.cache_clear()
    Base.metadata.create_all(get_engine())


@pytest.fixture(autouse=True)
def clean_settings():
    """Config comes from the process env only (never a local .env), and the
    cached settings/engine never leak across tests."""
    Settings.model_config["env_file"] = None
    get_settings.cache_clear()
    get_engine.cache_clear()
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()


def deal(**overrides) -> FlightDeal:
    """A FlightDeal with sensible defaults; override any field per test."""
    fields: dict = {
        "price": 129.99,
        "currency": "EUR",
        "departure_city": "Frankfurt",
        "departure_iata": "FRA",
        "arrival_city": "Helsinki",
        "arrival_iata": "HEL",
        "arrival_country": "Finland",
        "departs_at": datetime(2026, 9, 3, 10, 40),
        "returns_at": datetime(2026, 9, 8, 18, 5),
        "duration_minutes": 155,
        "link": "https://kiwi.com/deep",
    }
    fields.update(overrides)
    return FlightDeal(**fields)


def sent(
    subscriber_id: int = 1,
    source: str = "favorite",
    score: float = 160.0,
    savings_percent: int | None = None,
    usual_price: int | None = None,
    sent_at: datetime | None = None,
    **deal_overrides,
) -> SentDeal:
    """A SentDeal row built from deal(), the way record_sent_deals does.

    sent_at=None leaves the stamp to the DB server default (i.e. "just now")."""
    flight = deal(**deal_overrides)
    return SentDeal(
        subscriber_id=subscriber_id,
        source=source,
        score=score,
        quality_score=deal_score(flight),
        origin_iata=flight.departure_iata,
        savings_percent=savings_percent,
        usual_price=usual_price,
        sent_at=sent_at,
        **flight.model_dump(include=SENT_FIELDS),
    )


def observation(
    search_id: str = "s1",
    origin_iata: str = "FRA",
    stopovers: int = 0,
    observed_at: datetime = datetime(2026, 8, 25, 6, 0),
    **deal_overrides,
) -> PriceObservation:
    """A PriceObservation built from deal(), the way RecordingProvider does."""
    return PriceObservation(
        search_id=search_id,
        origin_iata=origin_iata,
        stopovers=stopovers,
        observed_at=observed_at,
        **deal(**deal_overrides).model_dump(include=OBSERVED_FIELDS),
    )
