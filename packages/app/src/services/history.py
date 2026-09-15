"""Append-only deal history: every candidate seen and every deal emailed.

Written silently from the digest job; read back for lowest-price claims and
freshness features. No aggregation at write time."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import func, select, tuple_

from src.db import PriceObservation, SentDeal, insert_rows, session_scope
from src.models.flights import FlightDeal, RankedDeal, SearchQuery
from src.models.history import SentHistory
from src.services.providers import FlightProvider
from src.services.selection import Observation, deal_score

OBSERVATION_WINDOW_WEEKS = 26
FRESHNESS_WINDOW_WEEKS = 8


def _utcnow() -> datetime:
    """UTC-fixed like tequila's epoch decoding: immune to host TZ and DST."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


OBSERVED_FIELDS = {
    "arrival_iata",
    "arrival_country",
    "price",
    "currency",
    "price_eur",
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
    "price_eur",
    "link",
}


class RecordingProvider:
    """Wraps a provider and logs every candidate it returns.

    started_at marks the run boundary: every observation this instance writes
    is stamped at or after it by the same clock (not the DB server default,
    whose clock can sit behind), so route_observations(before=started_at) sees
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


def route_observations(
    routes: set[tuple[str, str]], before: datetime
) -> dict[tuple[str, str], list[Observation]]:
    """EUR price observations per (origin, arrival) route over the rolling
    window, for selection.price_low_since to interpret.

    Keyed per departure airport — the same arrival can price very differently
    from different origins. The pool is shared across subscribers and
    currencies: every observation carries the provider's EUR conversion.
    Only observations strictly before `before` are returned (pass the run
    start, so a run's own candidates never anchor themselves)."""
    statement = select(
        PriceObservation.origin_iata,
        PriceObservation.arrival_iata,
        PriceObservation.observed_at,
        PriceObservation.price_eur,
    ).where(
        tuple_(PriceObservation.origin_iata, PriceObservation.arrival_iata).in_(routes),
        PriceObservation.observed_at
        >= before - timedelta(weeks=OBSERVATION_WINDOW_WEEKS),
        PriceObservation.observed_at < before,
    )
    observations: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    with session_scope() as session:
        for origin_iata, arrival_iata, observed_at, price_eur in session.execute(
            statement
        ):
            observations[(origin_iata, arrival_iata)].append((observed_at, price_eur))
    return dict(observations)


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


def record_sent_deals(subscriber_id: int, deals: list[RankedDeal]) -> None:
    rows = [
        SentDeal(
            subscriber_id=subscriber_id,
            source=ranked.source,
            score=ranked.score,
            # Deterministically recomputed since ranked.score is freshness-inflated
            quality_score=deal_score(ranked.deal),
            origin_iata=ranked.origin_iata,
            reason=ranked.reason,
            **ranked.deal.model_dump(include=SENT_FIELDS),
        )
        for ranked in deals
    ]
    insert_rows(rows)
