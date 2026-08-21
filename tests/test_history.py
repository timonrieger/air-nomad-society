from datetime import datetime, timedelta

from src.app.db import PriceObservation, insert_rows
from src.app.models.history import SentHistory
from src.app.services.history import (
    BASELINE_WINDOW_WEEKS,
    FRESHNESS_WINDOW_WEEKS,
    _utcnow,
    route_baselines,
    sent_history,
)
from tests.conftest import observation, sent

RUN_STARTED = datetime(2026, 9, 1, 6, 0)
NOW = _utcnow()


def spread(prices: tuple[float, ...], **overrides) -> list[PriceObservation]:
    """One observation per price, each on its own day inside the window."""
    return [
        observation(
            price=price,
            observed_at=datetime(2026, 8, 1, 6, 0) + timedelta(days=index),
            **overrides,
        )
        for index, price in enumerate(prices)
    ]


def baselines(
    routes: set[tuple[str, str]] | None = None,
) -> dict[tuple[str, str], float]:
    return route_baselines(routes or {("FRA", "HEL")}, "EUR", before=RUN_STARTED)


def test_median_over_window(sqlite_db) -> None:
    insert_rows(spread((100, 200, 300, 400)))
    assert baselines() == {("FRA", "HEL"): 250.0}


def test_routes_below_minimum_days_are_omitted(sqlite_db) -> None:
    insert_rows(spread((100, 200, 300)))
    assert baselines() == {}


def test_single_day_of_observations_does_not_anchor(sqlite_db) -> None:
    # Four rows, one day: a snapshot, not history.
    insert_rows([observation(price=price) for price in (100, 200, 300, 400)])
    assert baselines() == {}


def test_multi_origin_routes_do_not_cross_pollinate(sqlite_db) -> None:
    # FRA→TKU sits inside the IN-filter cross product of the requested
    # routes but is neither of them; it must not mint a baseline.
    insert_rows(
        spread((100, 200, 300, 400))
        + spread((500, 600, 700, 800), origin_iata="BER", arrival_iata="TKU")
        + spread((999, 999, 999, 999), arrival_iata="TKU")
    )
    assert baselines({("FRA", "HEL"), ("BER", "TKU")}) == {
        ("FRA", "HEL"): 250.0,
        ("BER", "TKU"): 650.0,
    }


def test_only_matching_route_and_currency_count(sqlite_db) -> None:
    insert_rows(
        spread((100, 200, 300, 400))
        + spread((999, 999, 999, 999), currency="USD")
        + spread((999, 999, 999, 999), origin_iata="BER")
        + spread((999, 999, 999, 999), arrival_iata="TKU")
    )
    assert baselines() == {("FRA", "HEL"): 250.0}


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
        spread((100, 200, 300, 400))
        + [observation(price=999, observed_at=RUN_STARTED)]
        + [
            observation(
                price=999,
                observed_at=RUN_STARTED - timedelta(weeks=BASELINE_WINDOW_WEEKS + 1),
            )
        ]
    )
    assert baselines() == {("FRA", "HEL"): 250.0}
