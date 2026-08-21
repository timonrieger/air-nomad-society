from typing import Any

import httpx2

from src.models.flights import FlightDeal, SearchQuery


class ResponseStub:
    """A canned httpx2.Response: json body plus status code."""

    def __init__(self, body: dict[str, Any], status_code: int = 200) -> None:
        self.body = body
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self.body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx2.HTTPError(f"status {self.status_code}")


class FakeProvider:
    """In-memory FlightProvider: maps (origin, destination) IATAs to candidates."""

    def __init__(
        self, deals: dict[tuple[str, str], list[FlightDeal]] | None = None
    ) -> None:
        self.deals = deals or {}
        self.queries: list[SearchQuery] = []

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        self.queries.append(query)
        return self.deals.get((query.origin_iata, query.destination_iata), [])[:count]
