"""Builds one subscriber's digest: deals for their favorite countries plus
randomly picked "secret gem" countries."""

import logging
import random
from datetime import date, timedelta

from pydantic import BaseModel

from src.app.models.subscriber import Subscriber
from src.app.models.flights import FlightDeal, SearchQuery
from src.app.services.providers import FlightProvider
from src.app.services.refdata import Country
from src.app.services.selection import favorite_destinations, select_gems

logger = logging.getLogger(__name__)


class DigestResult(BaseModel):
    dream_deals: list[FlightDeal]
    gem_deals: list[FlightDeal]


def build_digest(
    subscriber: Subscriber,
    provider: FlightProvider,
    destinations: list[Country],
    rng: random.Random | None = None,
    today: date | None = None,
) -> DigestResult:
    start = today or date.today()

    def deals_for(countries: list[Country]) -> list[FlightDeal]:
        deals = []
        for country in countries:
            query = SearchQuery(
                origin_iata=subscriber.departure_iata,
                destination_iata=country.code,
                date_from=start + timedelta(days=subscriber.min_days_ahead),
                date_to=start + timedelta(days=subscriber.max_days_ahead),
                min_nights=subscriber.min_nights,
                max_nights=subscriber.max_nights,
                currency=subscriber.currency,
            )
            deal = provider.search_cheapest(query)
            # The cheapest destination in a country can be the origin city
            # itself (e.g. searching Germany from Frankfurt); skip those.
            if deal and deal.departure_city != deal.arrival_city:
                deals.append(deal)
        return deals

    favorites = set(subscriber.favorites)
    dream_deals = deals_for(favorite_destinations(destinations, favorites))
    gems = select_gems(destinations, favorites, set(subscriber.excluded), rng=rng)
    gem_deals = deals_for(gems)
    logger.info(
        "digest for %s: %d dream deals, %d gem deals",
        subscriber.email,
        len(dream_deals),
        len(gem_deals),
    )
    return DigestResult(dream_deals=dream_deals, gem_deals=gem_deals)
