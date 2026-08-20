from datetime import datetime, timedelta

from src.app.db import PriceObservation, insert_rows
from src.app.services.history import BASELINE_WINDOW_WEEKS, route_baselines

RUN_STARTED = datetime(2026, 9, 1, 6, 0)


def observation(**overrides) -> PriceObservation:
    fields: dict = {
        "search_id": "s1",
        "origin_iata": "FRA",
        "arrival_iata": "HEL",
        "arrival_country": "Finland",
        "price": 100.0,
        "currency": "EUR",
        "departs_at": datetime(2026, 9, 3, 10, 40),
        "returns_at": datetime(2026, 9, 8, 18, 5),
        "duration_minutes": 155,
        "stopovers": 0,
        "observed_at": RUN_STARTED - timedelta(weeks=1),
    }
    fields.update(overrides)
    return PriceObservation(**fields)


def baselines(arrival_iatas: set[str] | None = None) -> dict[str, float]:
    return route_baselines("FRA", arrival_iatas or {"HEL"}, "EUR", before=RUN_STARTED)


def test_median_over_window(sqlite_db) -> None:
    insert_rows([observation(price=price) for price in (100, 200, 300, 400)])
    assert baselines() == {"HEL": 250.0}


def test_routes_below_minimum_observations_are_omitted(sqlite_db) -> None:
    insert_rows([observation(price=price) for price in (100, 200, 300)])
    assert baselines() == {}


def test_only_matching_route_and_currency_count(sqlite_db) -> None:
    insert_rows(
        [observation(price=price) for price in (100, 200, 300, 400)]
        + [observation(price=999, currency="USD")]
        + [observation(price=999, origin_iata="BER")]
        + [observation(price=999, arrival_iata="TKU")]
    )
    assert baselines() == {"HEL": 250.0}


def test_current_run_and_stale_observations_are_excluded(sqlite_db) -> None:
    insert_rows(
        [observation(price=price) for price in (100, 200, 300, 400)]
        + [observation(price=999, observed_at=RUN_STARTED)]
        + [
            observation(
                price=999,
                observed_at=RUN_STARTED - timedelta(weeks=BASELINE_WINDOW_WEEKS + 1),
            )
        ]
    )
    assert baselines() == {"HEL": 250.0}
