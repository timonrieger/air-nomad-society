from typing import Protocol

from src.models.flights import FlightDeal, SearchQuery


class FlightProvider(Protocol):
    """Anything that can find the cheapest round trip for a query."""

    def search_cheapest(self, query: SearchQuery) -> FlightDeal | None: ...
