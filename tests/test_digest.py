import random
from datetime import date

from src.app.db import AirNomads
from src.app.models.subscriber import Subscriber
from src.app.services.digest import build_digest
from src.app.models.history import SentHistory
from src.app.services.selection import deal_score
from src.app.services.refdata import Country
from tests.conftest import deal
from tests.fakes import FakeProvider


def digest(subscriber, provider, history=None, baselines=None, rng=None, today=None):
    """build_digest with the test defaults spelled once."""
    return build_digest(
        subscriber,
        provider,
        DESTINATIONS,
        history or SentHistory(),
        baselines_for=lambda routes: baselines or {},
        rng=rng or random.Random(1),
        today=today,
    )


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
    departure_airports=["FRA"],
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
            ("FRA", "FI"): [deal(price=200)],
            ("FRA", "ES"): [
                deal(
                    price=90,
                    arrival_iata="ES",
                    arrival_city="Palma",
                    arrival_country="Spain",
                )
            ],
        }
    )
    result = digest(SUBSCRIBER, provider, rng=random.Random(7))
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
    cheap_stopover = deal(price=100, via_cities=["Riga"])
    direct = deal(price=110)
    provider = FakeProvider({("FRA", "FI"): [cheap_stopover, direct]})
    result = digest(SUBSCRIBER, provider)
    finland = [r for r in result.deals if r.deal.arrival_country == "Finland"]
    assert finland[0].deal == direct
    # The beaten candidate rides along as a runner-up for the reasoning line.
    assert [r.deal for r in finland[0].runner_ups] == [cheap_stopover]


def test_repeating_favorite_prefers_a_fresh_city() -> None:
    helsinki = deal(price=100)
    turku = deal(price=104, arrival_iata="TKU", arrival_city="Turku")
    provider = FakeProvider({("FRA", "FI"): [helsinki, turku]})
    history = SentHistory(
        recent_countries={"Finland"},
        recent_cities={"HEL"},
        all_countries={"Finland"},
    )
    result = digest(SUBSCRIBER, provider, history=history)
    finland = [r for r in result.deals if r.deal.arrival_country == "Finland"]
    # Helsinki is slightly cheaper but was just sent; Turku is fresh.
    assert finland[0].deal == turku
    assert finland[0].first_time is False


def test_clearly_below_typical_repeats_without_penalty() -> None:
    # HEL was just sent, but 129.99 is ≥15% under its 310 typical price —
    # the repeat escapes both penalties and the baseline reaches the result.
    provider = FakeProvider({("FRA", "FI"): [deal()]})
    history = SentHistory(
        recent_countries={"Finland"},
        recent_cities={"HEL"},
        all_countries={"Finland"},
    )
    typical = {("FRA", "HEL"): 310.0}
    result = digest(SUBSCRIBER, provider, history=history, baselines=typical)
    finland = [r for r in result.deals if r.deal.arrival_country == "Finland"]
    assert finland[0].score == deal_score(finland[0].deal)
    assert result.baselines == typical


def test_first_time_country_is_flagged_once_history_exists() -> None:
    provider = FakeProvider({("FRA", "FI"): [deal()]})
    seen_spain = SentHistory(all_countries={"Spain"})
    result = digest(SUBSCRIBER, provider, history=seen_spain)
    finland = [r for r in result.deals if r.deal.arrival_country == "Finland"]
    assert finland[0].first_time is True


def test_brand_new_subscribers_get_no_first_time_flags() -> None:
    # With no history at all, badging every card would say nothing.
    provider = FakeProvider({("FRA", "FI"): [deal()]})
    result = digest(SUBSCRIBER, provider)
    finland = [r for r in result.deals if r.deal.arrival_country == "Finland"]
    assert finland[0].first_time is False


def test_searches_fan_out_per_departure_airport() -> None:
    subscriber = SUBSCRIBER.model_copy(update={"departure_airports": ["FRA", "BER"]})
    provider = FakeProvider({("FRA", "FI"): [deal()]})
    digest(subscriber, provider)
    finland_queries = [q for q in provider.queries if q.destination_iata == "FI"]
    assert [q.origin_iata for q in finland_queries] == ["FRA", "BER"]


def test_best_deal_across_airports_wins_and_keeps_its_origin() -> None:
    subscriber = SUBSCRIBER.model_copy(update={"departure_airports": ["FRA", "BER"]})
    frankfurt = deal(price=140)
    berlin = deal(price=120, departure_city="Berlin", departure_iata="BER")
    provider = FakeProvider({("FRA", "FI"): [frankfurt], ("BER", "FI"): [berlin]})
    result = digest(subscriber, provider)
    finland = [r for r in result.deals if r.deal.arrival_country == "Finland"]
    assert finland[0].deal == berlin
    assert finland[0].origin_iata == "BER"
    assert [r.deal for r in finland[0].runner_ups] == [frankfurt]


def test_search_window_derives_from_subscriber() -> None:
    provider = FakeProvider()
    result = digest(SUBSCRIBER, provider, today=date(2026, 1, 1))
    assert result.window_start == date(2026, 1, 11)
    assert result.window_end == date(2026, 2, 10)
    query = provider.queries[0]
    assert query.date_from == date(2026, 1, 11)
    assert query.date_to == date(2026, 2, 10)
    assert query.min_nights == 3 and query.max_nights == 7
    assert query.origin_iata == "FRA"


def test_same_city_deals_are_dropped() -> None:
    provider = FakeProvider({("FRA", "FI"): [deal(arrival_city="Frankfurt")]})
    result = digest(SUBSCRIBER, provider)
    assert result.deals == []


def test_deals_to_another_departure_city_are_dropped() -> None:
    # A FRA+BER subscriber must not be sold a "deal" to Berlin.
    subscriber = SUBSCRIBER.model_copy(update={"departure_airports": ["FRA", "BER"]})
    to_berlin = deal(arrival_iata="BER", arrival_city="Berlin")
    provider = FakeProvider({("FRA", "FI"): [to_berlin]})
    result = digest(subscriber, provider)
    assert result.deals == []


def test_subscriber_from_row_parses_country_lists() -> None:
    row = AirNomads(
        id=3,
        username="t",
        email="t@example.com",
        departure_airports="BER,MUC",
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
    assert subscriber.departure_airports == ["BER", "MUC"]
    assert subscriber.favorites == ["Finland", "Spain"]
    assert subscriber.excluded == []
    assert subscriber.confirmed is False
    assert subscriber.currency == "EUR"
