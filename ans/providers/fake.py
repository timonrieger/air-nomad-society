from ans.models import FlightDeal, SearchQuery


class FakeProvider:
    """In-memory FlightProvider for tests: maps destination IATA -> deal."""

    def __init__(self, deals: dict[str, FlightDeal] | None = None) -> None:
        self.deals = deals or {}
        self.queries: list[SearchQuery] = []

    def search_cheapest(self, query: SearchQuery) -> FlightDeal | None:
        self.queries.append(query)
        return self.deals.get(query.destination_iata)
