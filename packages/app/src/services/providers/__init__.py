from typing import Protocol

from src.models.flights import FlightDeal, SearchQuery
from src.services.refdata import City, Country


class FlightProvider(Protocol):
    """Anything that can find round-trip candidates for a query."""

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        """Up to `count` itineraries, cheapest first."""


class OriginRouter:
    """Sends each search to every provider its origin city lists; one
    provider's candidates never hide another's."""

    def __init__(
        self, providers: dict[str, FlightProvider], cities: list[City]
    ) -> None:
        self._providers = {
            city.code: [providers[name] for name in city.providers] for city in cities
        }

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        return [
            deal
            for provider in self._providers[query.origin_iata]
            for deal in provider.search_top(query, count)
        ]


class LocationSource(Protocol):
    """Anything that can list the cities and countries it searches."""

    name: str

    def locations(self, city_limit: int) -> tuple[list[City], list[Country]]:
        """Up to `city_limit` departure cities, most popular first, and the
        destination countries."""
