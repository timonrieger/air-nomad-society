import logging
import time
from datetime import datetime
from typing import Any

import requests

from src.app.models.flights import FlightDeal, SearchQuery

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
RATE_LIMIT_ATTEMPTS = 2
RATE_LIMIT_WAIT = 10
MAX_STOPOVERS = 1


class TequilaProvider:
    """Searches flights via Kiwi's Tequila API.

    One price-sorted search per destination, allowing up to one stopover
    per sector; picking the best candidate is the caller's job.
    """

    def __init__(self, endpoint: str, api_key: str) -> None:
        self.endpoint = endpoint
        # One keep-alive session for the whole run: every search hits the
        # same host, so this saves a TLS handshake per request.
        self._session = requests.Session()
        self._session.headers["apikey"] = api_key

    def search_top(self, query: SearchQuery, count: int) -> list[FlightDeal]:
        itineraries = self._search(query, count)
        return [self._to_deal(itinerary, query.currency) for itinerary in itineraries]

    def _search(self, query: SearchQuery, count: int) -> list[dict[str, Any]]:
        params = {
            "fly_from": query.origin_iata,
            "fly_to": query.destination_iata,
            "date_from": query.date_from.strftime("%d/%m/%Y"),
            "date_to": query.date_to.strftime("%d/%m/%Y"),
            "nights_in_dst_from": query.min_nights,
            "nights_in_dst_to": query.max_nights,
            "max_sector_stopovers": MAX_STOPOVERS,
            "limit": count,
            "curr": query.currency,
        }
        # A response without a "data" key means we got rate limited: back off
        # and retry before giving up on the destination.
        for attempt in range(RATE_LIMIT_ATTEMPTS):
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
        outbound_stop = route[0]["flyTo"] != data["flyTo"]
        return FlightDeal(
            price=data["price"],
            currency=currency,
            departure_city=data["cityFrom"],
            departure_iata=data["flyFrom"],
            arrival_city=data["cityTo"],
            arrival_iata=data["flyTo"],
            arrival_country=data["countryTo"]["name"],
            departs_at=datetime.fromtimestamp(route[0]["dTime"]),
            returns_at=datetime.fromtimestamp(route[-1]["aTime"]),
            duration_minutes=data["duration"]["departure"] // 60,
            stopovers=int(outbound_stop),
            link=data["deep_link"],
            via_city=route[0]["cityTo"] if outbound_stop else None,
        )
