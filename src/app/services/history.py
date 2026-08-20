"""Append-only deal history: every candidate seen and every deal emailed.

Written silently from the digest job; read later by the price anchor and
freshness features. No aggregation at write time."""

from uuid import uuid4

from src.app.db import PriceObservation, SentDeal, insert_rows
from src.app.models.flights import FlightDeal, RankedDeal, SearchQuery
from src.app.services.providers import FlightProvider

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
    """Wraps a provider and logs every candidate it returns."""

    def __init__(self, inner: FlightProvider) -> None:
        self.inner = inner

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        deals = self.inner.search_top(query, count)
        search_id = str(uuid4())
        insert_rows(
            [
                PriceObservation(
                    search_id=search_id,
                    origin_iata=query.origin_iata,
                    stopovers=len(deal.via_cities) + len(deal.return_via_cities),
                    **deal.model_dump(include=OBSERVED_FIELDS),
                )
                for deal in deals
            ]
        )
        return deals


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
