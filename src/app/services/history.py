"""Append-only deal history: every candidate seen and every deal emailed.

Written silently from the digest job; read back for the price anchor and
freshness features. No aggregation at write time."""

from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median
from uuid import uuid4

from sqlalchemy import select

from src.app.db import PriceObservation, SentDeal, insert_rows, session_scope
from src.app.models.flights import FlightDeal, RankedDeal, SearchQuery
from src.app.services.providers import FlightProvider

BASELINE_WINDOW_WEEKS = 26
MIN_OBSERVATIONS = 4

OBSERVED_FIELDS = {
    "arrival_iata",
    "arrival_country",
    "price",
    "currency",
    "departs_at",
    "returns_at",
    "duration_minutes",
}


class RecordingProvider:
    """Wraps a provider and logs every candidate it returns.

    started_at marks the run boundary: every observation this instance writes
    is stamped at or after it by the same clock (not the DB server default,
    whose clock can sit behind), so route_baselines(before=started_at) sees
    exactly the earlier runs."""

    def __init__(self, inner: FlightProvider) -> None:
        self.inner = inner
        self.started_at = datetime.now()

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        deals = self.inner.search_top(query, count)
        search_id = str(uuid4())
        observed_at = datetime.now()
        insert_rows(
            [
                PriceObservation(
                    search_id=search_id,
                    origin_iata=query.origin_iata,
                    stopovers=deal.stopovers,
                    observed_at=observed_at,
                    **deal.model_dump(include=OBSERVED_FIELDS),
                )
                for deal in deals
            ]
        )
        return deals


def route_baselines(
    origin_iata: str, arrival_iatas: set[str], currency: str, before: datetime
) -> dict[str, float]:
    """Median observed price per arrival city over the rolling window.

    Only observations strictly before `before` count (pass the run start, so a
    run's own candidates never anchor themselves), and only in the subscriber's
    currency (prices in different currencies are not comparable). Routes with
    fewer than MIN_OBSERVATIONS observations are omitted — no anchor beats a
    shaky one."""
    statement = select(PriceObservation.arrival_iata, PriceObservation.price).where(
        PriceObservation.origin_iata == origin_iata,
        PriceObservation.arrival_iata.in_(arrival_iatas),
        PriceObservation.currency == currency,
        PriceObservation.observed_at >= before - timedelta(weeks=BASELINE_WINDOW_WEEKS),
        PriceObservation.observed_at < before,
    )
    prices: dict[str, list[float]] = defaultdict(list)
    with session_scope() as session:
        for arrival_iata, price in session.execute(statement):
            prices[arrival_iata].append(price)
    return {
        arrival_iata: median(values)
        for arrival_iata, values in prices.items()
        if len(values) >= MIN_OBSERVATIONS
    }


def record_sent_deals(subscriber_id: int, deals: list[RankedDeal]) -> None:
    insert_rows(
        [
            SentDeal(
                subscriber_id=subscriber_id,
                source=ranked.source,
                score=ranked.score,
                **ranked.deal.model_dump(
                    include={
                        "departure_iata",
                        "arrival_iata",
                        "arrival_country",
                        "price",
                        "currency",
                    }
                ),
            )
            for ranked in deals
        ]
    )
