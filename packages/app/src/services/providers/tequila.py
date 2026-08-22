import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

import httpx2

from src.models.flights import FlightDeal, SearchQuery

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
RATE_LIMIT_ATTEMPTS = 2
RATE_LIMIT_WAIT = 10
RATE_LIMIT_PER_MINUTE = 30


def _local(epoch: int) -> datetime:
    """Tequila's dTime/aTime are local wall times encoded as UTC epochs, so
    decoding must be UTC-fixed — the host timezone would shift the clock."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).replace(tzinfo=None)


class TequilaProvider:
    """Searches flights via Kiwi's Tequila API.

    Two price-sorted searches per destination — direct-only, then up to one
    stopover per sector — each returning the cheapest itinerary per city.
    Picking the best candidate is the caller's job.
    """

    def __init__(self, endpoint: str, api_key: str) -> None:
        self.endpoint = endpoint
        self._session = httpx2.Client()
        self._session.headers["apikey"] = api_key
        self._request_times: deque[float] = deque(maxlen=RATE_LIMIT_PER_MINUTE)

    def _pace(self) -> None:
        """The quota-th-latest request must be a minute old before the next."""
        if len(self._request_times) == RATE_LIMIT_PER_MINUTE:
            wait = 60 - (time.monotonic() - self._request_times[0])
            if wait > 0:
                time.sleep(wait)
        self._request_times.append(time.monotonic())

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        # The direct-only pass is not redundant: in a single price-sorted
        # search, `count` one-stop fares can bury every direct option.
        itineraries: dict[Any, dict[str, Any]] = {}
        for max_stopovers in (0, 1):
            for itinerary in self._search(query, max_stopovers, count):
                itineraries.setdefault(itinerary["id"], itinerary)
        return [
            self._to_deal(itinerary, query.currency)
            for itinerary in itineraries.values()
        ]

    def _search(
        self, query: SearchQuery, max_stopovers: int, count: int
    ) -> list[dict[str, Any]]:
        params = {
            "fly_from": query.origin_iata,
            "fly_to": query.destination_iata,
            "date_from": query.date_from.strftime("%d/%m/%Y"),
            "date_to": query.date_to.strftime("%d/%m/%Y"),
            "nights_in_dst_from": query.min_nights,
            "nights_in_dst_to": query.max_nights,
            "one_for_city": 1,
            "max_sector_stopovers": max_stopovers,
            "limit": count,
            "curr": query.currency,
        }
        for attempt in range(RATE_LIMIT_ATTEMPTS):
            self._pace()
            response = self._session.get(
                f"{self.endpoint}/search", params=params, timeout=REQUEST_TIMEOUT
            )
            body = response.json()
            if "data" in body:
                return body["data"]
            if attempt < RATE_LIMIT_ATTEMPTS - 1:
                logger.warning(
                    "tequila returned no data for %s->%s (status %s), retrying",
                    query.origin_iata,
                    query.destination_iata,
                    response.status_code,
                )
                time.sleep(RATE_LIMIT_WAIT)
        return []

    @staticmethod
    def _to_deal(data: dict[str, Any], currency: str) -> FlightDeal:
        route = data["route"]
        outbound = [leg for leg in route if leg["return"] == 0]
        inbound = [leg for leg in route if leg["return"] == 1]
        return FlightDeal(
            price=data["price"],
            currency=currency,
            departure_city=data["cityFrom"],
            departure_iata=data["flyFrom"],
            arrival_city=data["cityTo"],
            arrival_iata=data["flyTo"],
            arrival_country=data["countryTo"]["name"],
            departs_at=_local(outbound[0]["dTime"]),
            returns_at=_local(route[-1]["aTime"]),
            duration_minutes=data["duration"]["departure"] // 60,
            via_cities=[leg["cityTo"] for leg in outbound[:-1]],
            return_via_cities=[leg["cityTo"] for leg in inbound[:-1]],
            link=data["deep_link"],
        )
