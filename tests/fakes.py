from src.app.models.flights import FlightDeal, SearchQuery


class FakeProvider:
    """In-memory FlightProvider for tests: maps destination IATA -> candidates."""

    def __init__(self, deals: dict[str, list[FlightDeal]] | None = None) -> None:
        self.deals = deals or {}
        self.queries: list[SearchQuery] = []

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        self.queries.append(query)
        return self.deals.get(query.destination_iata, [])[:count]
