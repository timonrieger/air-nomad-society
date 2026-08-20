import random
from datetime import date

from src.models.subscriber import Subscriber
from src.services.digest import build_digest
from src.models.flights import FlightDeal
from src.services.providers.fake import FakeProvider
from src.services.refdata import Country

DESTINATIONS = [
    Country(country="Finland", code="FI"),
    Country(country="Spain", code="ES"),
    Country(country="Japan", code="JP"),
    Country(country="Germany", code="DE"),
]

SUBSCRIBER = Subscriber(
    id=1,
    username="Timon",
    email="timon@example.com",
    departure_city="Frankfurt",
    departure_iata="FRA",
    currency="EUR",
    min_nights=3,
    max_nights=7,
    min_days_ahead=10,
    max_days_ahead=40,
    favorites=["Finland"],
    excluded=["Japan"],
)


def deal(code: str, arrival_city: str, country: str) -> FlightDeal:
    return FlightDeal(
        price=100,
        currency="EUR",
        departure_city="Frankfurt",
        departure_iata="FRA",
        arrival_city=arrival_city,
        arrival_iata=code,
        arrival_country=country,
        departs_on=date(2026, 9, 3),
        returns_on=date(2026, 9, 8),
        link="https://kiwi.com/x",
    )


def test_favorites_and_gems_split_correctly() -> None:
    provider = FakeProvider(
        {
            "FI": deal("FI", "Helsinki", "Finland"),
            "ES": deal("ES", "Palma", "Spain"),
        }
    )
    result = build_digest(SUBSCRIBER, provider, DESTINATIONS, rng=random.Random(7))
    assert [d.arrival_country for d in result.dream_deals] == ["Finland"]
    # Gems drawn from {Spain, Germany}: Finland is a favorite, Japan excluded.
    assert {d.arrival_country for d in result.gem_deals} <= {"Spain", "Germany"}
    gem_queries = {q.destination_iata for q in provider.queries} - {"FI"}
    assert gem_queries <= {"ES", "DE"}


def test_search_window_derives_from_subscriber() -> None:
    provider = FakeProvider()
    build_digest(
        SUBSCRIBER, provider, DESTINATIONS, rng=random.Random(1), today=date(2026, 1, 1)
    )
    query = provider.queries[0]
    assert query.date_from == date(2026, 1, 11)
    assert query.date_to == date(2026, 2, 10)
    assert query.min_nights == 3 and query.max_nights == 7
    assert query.origin_iata == "FRA"


def test_same_city_deals_are_dropped() -> None:
    provider = FakeProvider({"FI": deal("FI", "Frankfurt", "Finland")})
    result = build_digest(SUBSCRIBER, provider, DESTINATIONS, rng=random.Random(1))
    assert result.dream_deals == []


def test_subscriber_from_row_parses_country_lists() -> None:
    class Row:
        id = 3
        username = "t"
        email = "t@example.com"
        token = "tok"
        departure_city = "Berlin"
        departure_iata = "BER"
        currency = "eur"
        min_nights = 2
        max_nights = 5
        min_days_ahead = 1
        max_days_ahead = 30
        travel_countries = "Finland, Spain"
        excluded_countries = None

    subscriber = Subscriber.from_row(Row())
    assert subscriber.favorites == ["Finland", "Spain"]
    assert subscriber.excluded == []
    assert subscriber.currency == "EUR"
