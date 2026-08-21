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


def baselines(arrival_iatas: set[str] | None = None) -> dict[str, float]:
    return route_baselines("FRA", arrival_iatas or {"HEL"}, "EUR", before=RUN_STARTED)


def test_median_over_window(sqlite_db) -> None:
    insert_rows(spread((100, 200, 300, 400)))
    assert baselines() == {"HEL": 250.0}


def test_routes_below_minimum_days_are_omitted(sqlite_db) -> None:
    insert_rows(spread((100, 200, 300)))
    assert baselines() == {}


def test_single_day_of_observations_does_not_anchor(sqlite_db) -> None:
    # Four rows, one day: a snapshot, not history.
    insert_rows([observation(price=price) for price in (100, 200, 300, 400)])
    assert baselines() == {}


def test_only_matching_route_and_currency_count(sqlite_db) -> None:
    insert_rows(
        spread((100, 200, 300, 400))
        + spread((999, 999, 999, 999), currency="USD")
        + spread((999, 999, 999, 999), origin_iata="BER")
        + spread((999, 999, 999, 999), arrival_iata="TKU")
    )
    assert baselines() == {"HEL": 250.0}


def test_sent_history_splits_recent_from_ever(sqlite_db) -> None:
    outside_window = NOW - timedelta(weeks=FRESHNESS_WINDOW_WEEKS + 1)
    insert_rows(
        [
            sent(),
            sent(price=120),
            # Recently sent, but the old currency cannot gate the waiver.
            sent(price=90, currency="USD"),
            sent(arrival_country="Spain", arrival_iata="PMI", sent_at=outside_window),
        ]
    )
    history = sent_history(1, "EUR")
    assert history.recent_countries == {"Finland"}
    assert history.recent_country_prices == {"Finland": 120.0}
    assert history.recent_cities == {"HEL"}
    assert history.all_countries == {"Finland", "Spain"}


def test_sent_history_is_scoped_to_the_subscriber(sqlite_db) -> None:
    insert_rows([sent(subscriber_id=2)])
    assert sent_history(1, "EUR") == SentHistory()


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
    assert baselines() == {"HEL": 250.0}
