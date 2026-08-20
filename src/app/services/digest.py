"""Builds one subscriber's digest: the best-scoring deal per searched country
(favorites plus randomly picked "secret gem" countries), ranked into one list."""

import logging
import random
from datetime import date, timedelta

from pydantic import BaseModel

from src.app.models.subscriber import Subscriber
from src.app.models.flights import DealSource, RankedDeal, SearchQuery
from src.app.services.providers import FlightProvider
from src.app.services.refdata import Country
from src.app.services.selection import deal_score, favorite_destinations, select_gems

logger = logging.getLogger(__name__)

# Per stopover tier and city (the provider dedups per city), so this covers
# every destination city of a country with headroom to spare.
CANDIDATES_PER_COUNTRY = 30


class DigestResult(BaseModel):
    """Deals across all searched countries, best score first."""

    deals: list[RankedDeal]
    window_start: date
    window_end: date


def build_digest(
    subscriber: Subscriber,
    provider: FlightProvider,
    destinations: list[Country],
    rng: random.Random | None = None,
    today: date | None = None,
) -> DigestResult:
    start = today or date.today()
    window_start = start + timedelta(days=subscriber.min_days_ahead)
    window_end = start + timedelta(days=subscriber.max_days_ahead)

    def best_pick(country: Country, source: DealSource) -> RankedDeal | None:
        query = SearchQuery(
            origin_iata=subscriber.departure_iata,
            destination_iata=country.code,
            date_from=window_start,
            date_to=window_end,
            min_nights=subscriber.min_nights,
            max_nights=subscriber.max_nights,
            currency=subscriber.currency,
        )
        candidates = [
            deal
            for deal in provider.search_top(query, CANDIDATES_PER_COUNTRY)
            # A candidate's destination can be the origin city itself
            # (e.g. searching Germany from Frankfurt); skip those.
            if deal.departure_city != deal.arrival_city
        ]
        if not candidates:
            return None
        score, best = min(
            ((deal_score(deal), deal) for deal in candidates),
            key=lambda scored: scored[0],
        )
        return RankedDeal(deal=best, source=source, score=score)

    favorites = set(subscriber.favorites)
    gems = select_gems(destinations, favorites, set(subscriber.excluded), rng=rng)
    deals = [
        pick
        for country in favorite_destinations(destinations, favorites)
        if (pick := best_pick(country, "favorite"))
    ] + [pick for country in gems if (pick := best_pick(country, "discovery"))]
    deals.sort(key=lambda pick: pick.score)
    logger.info("digest for %s: %d deals", subscriber.email, len(deals))
    return DigestResult(deals=deals, window_start=window_start, window_end=window_end)
