"""Append-only deal history: every candidate seen and every deal emailed.

Written silently from the digest job; read back for the price anchor and
freshness features. No aggregation at write time."""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import median
from uuid import uuid4

from sqlalchemy import func, select

from src.db import PriceObservation, SentDeal, insert_rows, session_scope
from src.models.flights import FlightDeal, SearchQuery
from src.models.history import SentHistory
from src.services.digest import DigestResult
from src.services.providers import FlightProvider
from src.services.selection import deal_score, savings_percent

BASELINE_WINDOW_WEEKS = 26
MIN_OBSERVATION_DAYS = 4
FRESHNESS_WINDOW_WEEKS = 8


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

SENT_FIELDS = {
    "departure_city",
    "departure_iata",
    "arrival_city",
    "arrival_iata",
    "arrival_country",
    "price",
    "currency",
    "link",
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
        self._pending: list[PriceObservation] = []

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        deals = self.inner.search_top(query, count)
        search_id = str(uuid4())
        observed_at = _utcnow()
        self._pending += [
            PriceObservation(
                search_id=search_id,
                origin_iata=query.origin_iata,
                stopovers=deal.stopovers,
                observed_at=observed_at,
                **deal.model_dump(include=OBSERVED_FIELDS),
            )
            for deal in deals
        ]
        return deals

    def flush(self) -> None:
        """Flush in-memory observations"""
        insert_rows(self._pending)
        self._pending = []


def route_baselines(
    routes: set[tuple[str, str]], currency: str, before: datetime
) -> dict[tuple[str, str], float]:
    """Median observed price per (origin, arrival) route over the rolling window.

    Keyed per departure airport — the same arrival can price very differently
    from different origins. Only observations strictly before `before` count
    (pass the run start, so a run's own candidates never anchor themselves),
    and only in the subscriber's currency (prices in different currencies are
    not comparable). Routes observed on fewer than MIN_OBSERVATION_DAYS
    distinct days are omitted — a single day's snapshot is not history, and
    no anchor beats a shaky one."""
    statement = select(
        PriceObservation.origin_iata,
        PriceObservation.arrival_iata,
        PriceObservation.price,
        PriceObservation.observed_at,
    ).where(
        PriceObservation.origin_iata.in_({origin for origin, _ in routes}),
        PriceObservation.arrival_iata.in_({arrival for _, arrival in routes}),
        PriceObservation.currency == currency,
        PriceObservation.observed_at >= before - timedelta(weeks=BASELINE_WINDOW_WEEKS),
        PriceObservation.observed_at < before,
    )
    prices: dict[tuple[str, str], list[float]] = defaultdict(list)
    days: dict[tuple[str, str], set[date]] = defaultdict(set)
    with session_scope() as session:
        for origin_iata, arrival_iata, price, observed_at in session.execute(statement):
            route = (origin_iata, arrival_iata)
            # The two IN filters over-select pair combinations; keep exact routes.
            if route in routes:
                prices[route].append(price)
                days[route].add(observed_at.date())
    return {
        route: median(values)
        for route, values in prices.items()
        if len(days[route]) >= MIN_OBSERVATION_DAYS
    }


def last_sent_at(subscriber_id: int) -> datetime | None:
    """When this subscriber last received a digest with deals, if ever."""
    statement = select(func.max(SentDeal.sent_at)).where(
        SentDeal.subscriber_id == subscriber_id
    )
    with session_scope() as session:
        return session.scalar(statement)


def sent_history(subscriber_id: int) -> SentHistory:
    """The subscriber's sent-deal history as the freshness rules consume it."""
    cutoff = _utcnow() - timedelta(weeks=FRESHNESS_WINDOW_WEEKS)
    recent = select(SentDeal.arrival_country, SentDeal.arrival_iata).where(
        SentDeal.subscriber_id == subscriber_id, SentDeal.sent_at >= cutoff
    )
    ever = (
        select(SentDeal.arrival_country)
        .where(SentDeal.subscriber_id == subscriber_id)
        .distinct()
    )
    history = SentHistory()
    with session_scope() as session:
        history.all_countries.update(session.scalars(ever))
        for country, city in session.execute(recent):
            history.recent_countries.add(country)
            history.recent_cities.add(city)
    return history


def record_sent_deals(subscriber_id: int, digest: DigestResult) -> None:
    rows = []
    for ranked in digest.deals:
        baseline = digest.baseline_for(ranked)
        rows.append(
            SentDeal(
                subscriber_id=subscriber_id,
                source=ranked.source,
                score=ranked.score,
                # Deterministically recomputed since ranked.score is freshness-inflated
                quality_score=deal_score(ranked.deal),
                origin_iata=ranked.origin_iata,
                savings_percent=(
                    savings_percent(ranked.deal.price, baseline) if baseline else None
                ),
                usual_price=round(baseline) if baseline else None,
                reason=ranked.reason,
                **ranked.deal.model_dump(include=SENT_FIELDS),
            )
        )
    insert_rows(rows)
