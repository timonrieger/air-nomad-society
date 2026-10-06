from typing import Protocol

from src.models.flights import FlightDeal, SearchQuery
from src.services.refdata import City, Country


class FlightProvider(Protocol):
    """Anything that can find round-trip candidates for a query."""

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        """Up to `count` itineraries, cheapest first."""


class LocationSource(Protocol):
    """Anything that can list the cities and countries it searches."""

    def locations(self, city_limit: int) -> tuple[list[City], list[Country]]:
        """Up to `city_limit` departure cities, most popular first, and the
        destination countries."""
