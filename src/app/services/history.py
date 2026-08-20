"""Append-only deal history: every candidate seen and every deal emailed.

Written silently from the digest job; read later by the price anchor and
freshness features. No aggregation at write time."""

from src.app.db import PriceObservation, SentDeal, insert_rows
from src.app.models.flights import FlightDeal, RankedDeal, SearchQuery
from src.app.services.providers import FlightProvider


class RecordingProvider:
    """Wraps a provider and logs every candidate it returns."""

    def __init__(self, inner: FlightProvider) -> None:
        self.inner = inner

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        deals = self.inner.search_top(query, count)
        insert_rows([_observation(deal) for deal in deals])
        return deals


def _observation(deal: FlightDeal) -> PriceObservation:
    return PriceObservation(
        origin_iata=deal.departure_iata,
        destination_iata=deal.arrival_iata,
        arrival_country=deal.arrival_country,
        price=deal.price,
        currency=deal.currency,
        departs_at=deal.departs_at,
        returns_at=deal.returns_at,
    )


def record_sent_deals(subscriber_id: int, deals: list[RankedDeal]) -> None:
    insert_rows(
        [
            SentDeal(
                subscriber_id=subscriber_id,
                origin_iata=ranked.deal.departure_iata,
                destination_iata=ranked.deal.arrival_iata,
                arrival_country=ranked.deal.arrival_country,
                price=ranked.deal.price,
                currency=ranked.deal.currency,
                source=ranked.source,
                score=ranked.score,
            )
            for ranked in deals
        ]
    )
