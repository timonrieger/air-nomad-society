import logging
import time
from datetime import datetime
from typing import Any

import requests

from ans.models import FlightDeal, SearchQuery

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
RATE_LIMIT_ATTEMPTS = 2
RATE_LIMIT_WAIT = 10


class TequilaProvider:
    """Searches flights via Kiwi's Tequila API.

    Direct flights are preferred; if none exist the search is retried
    allowing one stopover per sector, mirroring the legacy behaviour.
    """

    def __init__(self, endpoint: str, api_key: str) -> None:
        self.endpoint = endpoint
        self.api_key = api_key

    def search_cheapest(self, query: SearchQuery) -> FlightDeal | None:
        for max_stopovers in (0, 1):
            itineraries = self._search(query, max_stopovers)
            if itineraries:
                return self._to_deal(itineraries[0], query.currency)
        return None

    def _search(self, query: SearchQuery, max_stopovers: int) -> list[dict[str, Any]]:
        params = {
            "fly_from": query.origin_iata,
            "fly_to": query.destination_iata,
            "date_from": query.date_from.strftime("%d/%m/%Y"),
            "date_to": query.date_to.strftime("%d/%m/%Y"),
            "nights_in_dst_from": query.min_nights,
            "nights_in_dst_to": query.max_nights,
            "one_for_city": 1,
            "max_sector_stopovers": max_stopovers,
            "curr": query.currency,
        }
        # A response without a "data" key means we got rate limited: back off
        # and retry before giving up on the destination.
        for attempt in range(RATE_LIMIT_ATTEMPTS):
            response = requests.get(
                f"{self.endpoint}/search",
                params=params,
                headers={"apikey": self.api_key},
                timeout=REQUEST_TIMEOUT,
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
            departs_on=datetime.fromtimestamp(route[0]["dTime"]).date(),
            returns_on=datetime.fromtimestamp(route[-1]["aTime"]).date(),
            link=data["deep_link"],
            via_city=route[0]["cityTo"] if outbound_stop else None,
        )
