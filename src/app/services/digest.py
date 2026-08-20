"""Builds one subscriber's digest: the best-scoring deal per searched country
(favorites plus randomly picked "secret gem" countries), ranked into one list."""

import logging
import random
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel

from src.app.models.subscriber import Subscriber
from src.app.models.flights import FlightDeal, SearchQuery
from src.app.services.providers import FlightProvider
from src.app.services.refdata import Country
from src.app.services.selection import (
    deal_score,
    favorite_destinations,
    pick_best,
    select_gems,
)

logger = logging.getLogger(__name__)

CANDIDATES_PER_COUNTRY = 10


class RankedDeal(BaseModel):
    deal: FlightDeal
    source: Literal["favorite", "discovery"]


class DigestResult(BaseModel):
    """Deals across all searched countries, best score first."""

    deals: list[RankedDeal]


def build_digest(
    subscriber: Subscriber,
    provider: FlightProvider,
    destinations: list[Country],
    rng: random.Random | None = None,
    today: date | None = None,
) -> DigestResult:
    start = today or date.today()

    def best_deal(country: Country) -> FlightDeal | None:
        query = SearchQuery(
            origin_iata=subscriber.departure_iata,
            destination_iata=country.code,
            date_from=start + timedelta(days=subscriber.min_days_ahead),
            date_to=start + timedelta(days=subscriber.max_days_ahead),
            min_nights=subscriber.min_nights,
            max_nights=subscriber.max_nights,
            currency=subscriber.currency,
        )
        candidates = [
            deal
            for deal in provider.search_top(query, CANDIDATES_PER_COUNTRY)
            # The cheapest destination in a country can be the origin city
            # itself (e.g. searching Germany from Frankfurt); skip those.
            if deal.departure_city != deal.arrival_city
        ]
        return pick_best(candidates)

    favorites = set(subscriber.favorites)
    gems = select_gems(destinations, favorites, set(subscriber.excluded), rng=rng)
    ranked = [
        RankedDeal(deal=deal, source=source)
        for source, countries in (
            ("favorite", favorite_destinations(destinations, favorites)),
            ("discovery", gems),
        )
        for country in countries
        if (deal := best_deal(country))
    ]
    ranked.sort(key=lambda ranked_deal: deal_score(ranked_deal.deal))
    logger.info("digest for %s: %d deals", subscriber.email, len(ranked))
    return DigestResult(deals=ranked)
