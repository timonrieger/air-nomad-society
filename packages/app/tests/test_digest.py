import random
from datetime import date, datetime, timedelta

from src.models.flights import LowClaim
from src.models.subscriber import Subscriber
from src.services.digest import DigestResult, build_digest
from src.models.history import SentHistory
from src.services.selection import deal_score
from src.services.refdata import Country
from tests.conftest import deal
from tests.fakes import FakeProvider

RUN_DAY = date(2026, 9, 1)
Observations = dict[tuple[str, str], list[tuple[datetime, float]]]


def digest(
    subscriber: Subscriber,
    provider: FakeProvider,
    history: SentHistory | None = None,
    observations: Observations | None = None,
    rng: random.Random | None = None,
    today: date | None = None,
) -> DigestResult:
    """build_digest with the test defaults spelled once."""
    return build_digest(
        subscriber,
        provider,
        DESTINATIONS,
        history or SentHistory(),
        observations_for=lambda routes: observations or {},
        rng=rng or random.Random(1),
        today=today,
    )


def weekly_lows(*prices: float, start: datetime = datetime(2026, 6, 1)):
    """One observation per price, a week apart — enough distinct days."""
    return [
        (start + timedelta(weeks=index), price) for index, price in enumerate(prices)
    ]


DESTINATIONS = [
    Country(country="Finland", code="FI", region="Europe"),
    Country(country="Spain", code="ES", region="Europe"),
    Country(country="Japan", code="JP", region="Asia"),
    Country(country="Germany", code="DE", region="Europe"),
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
    cadence="weekly",
    include_discoveries=True,
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


def test_long_standing_low_repeats_without_penalty() -> None:
    # HEL was just sent, but 129.99 has been the route's low since June —
    # the repeat escapes both penalties and the claim reaches the result.
    provider = FakeProvider({("FRA", "FI"): [deal()]})
    history = SentHistory(
        recent_countries={"Finland"},
        recent_cities={"HEL"},
        all_countries={"Finland"},
    )
    observations = {("FRA", "HEL"): weekly_lows(200, 210, 220, 230)}
    result = digest(
        SUBSCRIBER, provider, history=history, observations=observations, today=RUN_DAY
    )
    finland = [r for r in result.deals if r.deal.arrival_country == "Finland"]
    assert finland[0].score == deal_score(finland[0].deal)
    assert finland[0].low == LowClaim(since=datetime(2026, 6, 1), weeks=13)


def test_claims_are_measured_in_euros_for_non_eur_subscribers() -> None:
    # A 1430 SEK fare claims against the route's EUR observations via its
    # own EUR conversion.
    in_sek = deal(price=1430, currency="SEK", price_eur=130)
    provider = FakeProvider({("FRA", "FI"): [in_sek]})
    observations = {("FRA", "HEL"): weekly_lows(150, 160, 170, 125)}
    result = digest(SUBSCRIBER, provider, observations=observations, today=RUN_DAY)
    finland = [r for r in result.deals if r.deal.arrival_country == "Finland"]
    # The 125 EUR observation on Jun 22 undercuts it: the streak starts there.
    assert finland[0].low == LowClaim(since=datetime(2026, 6, 22), weeks=10)


def test_observations_fetched_for_waiver_candidates() -> None:
    # Finland is recently sent, so every Finland candidate route is
    # waiver-eligible; they already cover the winner — exactly one fetch.
    subscriber = SUBSCRIBER.model_copy(update={"departure_airports": ["FRA", "BER"]})
    berlin_deal = deal(price=200, departure_city="Berlin", departure_iata="BER")
    provider = FakeProvider({("FRA", "FI"): [deal()], ("BER", "FI"): [berlin_deal]})
    history = SentHistory(recent_countries={"Finland"}, all_countries={"Finland"})
    fetched: list[set[tuple[str, str]]] = []

    def lookup(routes: set[tuple[str, str]]) -> Observations:
        fetched.append(routes)
        return {}

    build_digest(
        subscriber, provider, DESTINATIONS, history, lookup, rng=random.Random(1)
    )
    assert fetched == [{("FRA", "HEL"), ("BER", "HEL")}]


def test_observations_topped_up_for_winners_outside_the_waiver() -> None:
    # Nothing recently sent → no waiver fetch; the winning route is still
    # fetched so the winner's lowest-price claim can be computed.
    provider = FakeProvider({("FRA", "FI"): [deal()]})
    fetched: list[set[tuple[str, str]]] = []

    def lookup(routes: set[tuple[str, str]]) -> Observations:
        fetched.append(routes)
        return {}

    build_digest(
        SUBSCRIBER, provider, DESTINATIONS, SentHistory(), lookup, rng=random.Random(1)
    )
    assert fetched == [{("FRA", "HEL")}]


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
    digest(SUBSCRIBER, provider, today=date(2026, 1, 1))
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


def test_no_favorites_searches_only_gems() -> None:
    provider = FakeProvider()
    digest(SUBSCRIBER.model_copy(update={"favorites": []}), provider)
    # Every non-excluded destination is gem-eligible, Finland included.
    assert {q.destination_iata for q in provider.queries} == {"FI", "ES", "DE"}


def test_discoveries_off_searches_only_favorites() -> None:
    provider = FakeProvider()
    digest(SUBSCRIBER.model_copy(update={"include_discoveries": False}), provider)
    assert [q.destination_iata for q in provider.queries] == ["FI"]
