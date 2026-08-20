import random
from datetime import date

from src.app.db import AirNomads
from src.app.models.subscriber import Subscriber
from src.app.services.digest import build_digest
from src.app.services.refdata import Country
from tests.conftest import deal
from tests.fakes import FakeProvider

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
    confirmed=True,
)


def test_favorites_and_discoveries_ranked_into_one_list() -> None:
    provider = FakeProvider(
        {
            "FI": [deal(price=200)],
            "ES": [
                deal(
                    price=90,
                    arrival_iata="ES",
                    arrival_city="Palma",
                    arrival_country="Spain",
                )
            ],
        }
    )
    result = build_digest(SUBSCRIBER, provider, DESTINATIONS, rng=random.Random(7))
    by_country = {r.deal.arrival_country: r.source for r in result.deals}
    assert by_country["Finland"] == "favorite"
    # Gems drawn from {Spain, Germany}: Finland is a favorite, Japan excluded.
    assert set(by_country) - {"Finland"} <= {"Spain", "Germany"}
    gem_queries = {q.destination_iata for q in provider.queries} - {"FI"}
    assert gem_queries <= {"ES", "DE"}
    # Both gems fit in the pool, so Spain is always searched; ranked by
    # score, the cheap Spain discovery outranks the Finland favorite.
    assert result.deals[0].deal.arrival_country == "Spain"
    assert result.deals[0].source == "discovery"


def test_best_scoring_candidate_wins_over_cheapest() -> None:
    cheap_stopover = deal(price=100, stopovers=1, via_city="Riga")
    direct = deal(price=110)
    provider = FakeProvider({"FI": [cheap_stopover, direct]})
    result = build_digest(SUBSCRIBER, provider, DESTINATIONS, rng=random.Random(1))
    finland = [r for r in result.deals if r.deal.arrival_country == "Finland"]
    assert finland[0].deal == direct


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
    provider = FakeProvider({"FI": [deal(arrival_city="Frankfurt")]})
    result = build_digest(SUBSCRIBER, provider, DESTINATIONS, rng=random.Random(1))
    assert result.deals == []


def test_subscriber_from_row_parses_country_lists() -> None:
    row = AirNomads(
        id=3,
        username="t",
        email="t@example.com",
        departure_city="Berlin",
        departure_iata="BER",
        currency="eur",
        min_nights=2,
        max_nights=5,
        min_days_ahead=1,
        max_days_ahead=30,
        travel_countries="Finland, Spain",
        excluded_countries=None,
        confirmed_at=None,
    )

    subscriber = Subscriber.from_row(row)
    assert subscriber.favorites == ["Finland", "Spain"]
    assert subscriber.excluded == []
    assert subscriber.confirmed is False
    assert subscriber.currency == "EUR"
