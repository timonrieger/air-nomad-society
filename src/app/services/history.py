"""Append-only deal history: every candidate seen and every deal emailed.

Written silently from the digest job; read back for the price anchor and
freshness features. No aggregation at write time."""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import median
from uuid import uuid4

from sqlalchemy import select

from src.app.db import PriceObservation, SentDeal, insert_rows, session_scope
from src.app.models.flights import FlightDeal, RankedDeal, SearchQuery
from src.app.services.providers import FlightProvider

BASELINE_WINDOW_WEEKS = 26
MIN_OBSERVATION_DAYS = 4


def _utcnow() -> datetime:
    """UTC-fixed like tequila's epoch decoding: immune to host TZ and DST."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
        self.started_at = _utcnow()

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        deals = self.inner.search_top(query, count)
        search_id = str(uuid4())
        observed_at = _utcnow()
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
    currency (prices in different currencies are not comparable). Routes
    observed on fewer than MIN_OBSERVATION_DAYS distinct days are omitted —
    a single day's snapshot is not history, and no anchor beats a shaky one."""
    statement = select(
        PriceObservation.arrival_iata,
        PriceObservation.price,
        PriceObservation.observed_at,
    ).where(
        PriceObservation.origin_iata == origin_iata,
        PriceObservation.arrival_iata.in_(arrival_iatas),
        PriceObservation.currency == currency,
        PriceObservation.observed_at >= before - timedelta(weeks=BASELINE_WINDOW_WEEKS),
        PriceObservation.observed_at < before,
    )
    prices: dict[str, list[float]] = defaultdict(list)
    days: dict[str, set[date]] = defaultdict(set)
    with session_scope() as session:
        for arrival_iata, price, observed_at in session.execute(statement):
            prices[arrival_iata].append(price)
            days[arrival_iata].add(observed_at.date())
    return {
        arrival_iata: median(values)
        for arrival_iata, values in prices.items()
        if len(days[arrival_iata]) >= MIN_OBSERVATION_DAYS
    }


def record_sent_deals(
    subscriber_id: int, deals: list[RankedDeal], reasons: dict[str, str]
) -> None:
    insert_rows(
        [
            SentDeal(
                subscriber_id=subscriber_id,
                source=ranked.source,
                score=ranked.score,
                reason=reasons.get(ranked.deal.arrival_iata),
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
