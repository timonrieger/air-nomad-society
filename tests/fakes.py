from typing import Any

import requests

from src.app.models.flights import FlightDeal, SearchQuery


class ResponseStub:
    """A canned requests.Response: json body plus status code."""

    def __init__(self, body: dict[str, Any], status_code: int = 200) -> None:
        self.body = body
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self.body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


class FakeProvider:
    """In-memory FlightProvider for tests.

    Keys are destination IATAs, or (origin, destination) pairs when a test
    cares which departure airport a candidate comes from."""

    def __init__(
        self,
        deals: dict[str | tuple[str, str], list[FlightDeal]] | None = None,
    ) -> None:
        self.deals = deals or {}
        self.queries: list[SearchQuery] = []

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        self.queries.append(query)
        route = (query.origin_iata, query.destination_iata)
        deals = self.deals.get(route, self.deals.get(query.destination_iata, []))
        return deals[:count]
