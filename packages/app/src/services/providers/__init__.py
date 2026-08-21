from typing import Protocol

from src.models.flights import FlightDeal, SearchQuery


class FlightProvider(Protocol):
    """Anything that can find round-trip candidates for a query."""

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        """Up to `count` itineraries, cheapest first."""
