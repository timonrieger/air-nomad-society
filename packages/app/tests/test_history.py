from datetime import datetime, timedelta

from src.db import PriceObservation, insert_rows
from src.models.history import SentHistory
from src.services.history import (
    FRESHNESS_WINDOW_WEEKS,
    OBSERVATION_WINDOW_WEEKS,
    _utcnow,
    route_observations,
    sent_history,
)
from tests.conftest import observation, sent

RUN_STARTED = datetime(2026, 9, 1, 6, 0)
FIRST_DAY = datetime(2026, 8, 1, 6, 0)
NOW = _utcnow()


def spread(prices: tuple[float, ...], **overrides) -> list[PriceObservation]:
    """One observation per price, each on its own day inside the window."""
    return [
        observation(
            price=price,
            observed_at=FIRST_DAY + timedelta(days=index),
            **overrides,
        )
        for index, price in enumerate(prices)
    ]


def observed(
    routes: set[tuple[str, str]] | None = None,
) -> dict[tuple[str, str], list[tuple[datetime, float]]]:
    return route_observations(routes or {("FRA", "HEL")}, before=RUN_STARTED)


def pairs(prices: tuple[float, ...]) -> list[tuple[datetime, float]]:
    """The (observed_at, price_eur) pairs spread() produces."""
    return [
        (FIRST_DAY + timedelta(days=index), price) for index, price in enumerate(prices)
    ]


def test_window_observations_returned_per_route(sqlite_db) -> None:
    insert_rows(spread((100, 200, 300)))
    assert observed() == {("FRA", "HEL"): pairs((100, 200, 300))}


def test_multi_origin_routes_do_not_cross_pollinate(sqlite_db) -> None:
    # FRA→TKU sits inside the IN-filter cross product of the requested
    # routes but is neither of them; its rows must not leak in.
    insert_rows(
        spread((100, 200))
        + spread((500, 600), origin_iata="BER", arrival_iata="TKU")
        + spread((999, 999), arrival_iata="TKU")
    )
    assert observed({("FRA", "HEL"), ("BER", "TKU")}) == {
        ("FRA", "HEL"): pairs((100, 200)),
        ("BER", "TKU"): pairs((500, 600)),
    }


def test_only_matching_routes_count(sqlite_db) -> None:
    insert_rows(
        spread((100, 200))
        + spread((999, 999), origin_iata="BER")
        + spread((999, 999), arrival_iata="TKU")
    )
    assert observed() == {("FRA", "HEL"): pairs((100, 200))}


def test_observations_pool_eur_values_across_currencies(sqlite_db) -> None:
    # EUR and USD subscribers observe the same route; the shared pool keeps
    # the provider's EUR conversions.
    usd_day = observation(
        price=330,
        currency="USD",
        price_eur=300,
        observed_at=datetime(2026, 8, 10, 6, 0),
    )
    insert_rows(spread((100, 200)) + [usd_day])
    assert observed() == {
        ("FRA", "HEL"): pairs((100, 200)) + [(datetime(2026, 8, 10, 6, 0), 300.0)]
    }


def test_sent_history_splits_recent_from_ever(sqlite_db) -> None:
    outside_window = NOW - timedelta(weeks=FRESHNESS_WINDOW_WEEKS + 1)
    insert_rows(
        [
            sent(),
            sent(price=120),
            sent(arrival_country="Spain", arrival_iata="PMI", sent_at=outside_window),
        ]
    )
    history = sent_history(1)
    assert history.recent_countries == {"Finland"}
    assert history.recent_cities == {"HEL"}
    assert history.all_countries == {"Finland", "Spain"}


def test_sent_history_is_scoped_to_the_subscriber(sqlite_db) -> None:
    insert_rows([sent(subscriber_id=2)])
    assert sent_history(1) == SentHistory()


def test_current_run_and_stale_observations_are_excluded(sqlite_db) -> None:
    insert_rows(
        spread((100, 200))
        + [observation(price=999, observed_at=RUN_STARTED)]
        + [
            observation(
                price=999,
                observed_at=RUN_STARTED - timedelta(weeks=OBSERVATION_WINDOW_WEEKS + 1),
            )
        ]
    )
    assert observed() == {("FRA", "HEL"): pairs((100, 200))}
