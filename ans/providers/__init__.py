from typing import Protocol

from ans.models import FlightDeal, SearchQuery


class FlightProvider(Protocol):
    """Anything that can find the cheapest round trip for a query.

    Kiwi's Tequila API is invitation-only for new partners, so the rest of
    the codebase depends on this protocol, never on Tequila directly.
    """

    def search_cheapest(self, query: SearchQuery) -> FlightDeal | None: ...
