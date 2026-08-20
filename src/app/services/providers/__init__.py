from typing import Protocol

from src.app.models.flights import FlightDeal, SearchQuery


class FlightProvider(Protocol):
    """Anything that can find the cheapest round trip for a query."""

    def search_cheapest(self, query: SearchQuery) -> FlightDeal | None: ...
