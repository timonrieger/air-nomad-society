import os
from datetime import date

import pytest

from src.app.config import Settings, get_settings
from src.app.db import get_engine
from src.app.models.flights import FlightDeal

# Required settings that have no default; tests never talk to real infra.
os.environ.setdefault("PUBLIC_BASE_URL", "http://localhost:5173")

TEST_SECRET = "test-secret-key-of-at-least-32-bytes!"  # gitleaks:allow


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


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)
    get_settings.cache_clear()


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
        "departs_on": date(2026, 9, 3),
        "returns_on": date(2026, 9, 8),
        "link": "https://kiwi.com/deep",
    }
    fields.update(overrides)
    return FlightDeal(**fields)
