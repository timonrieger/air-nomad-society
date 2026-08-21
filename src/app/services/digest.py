"""Builds one subscriber's digest: the best-scoring deal per searched country
(favorites plus randomly picked "secret gem" countries), ranked into one list."""

import logging
import random
from datetime import date, timedelta

from pydantic import BaseModel

from src.app.models.subscriber import Subscriber
from src.app.models.flights import DealSource, FlightDeal, RankedDeal, SearchQuery
from src.app.models.history import SentHistory
from src.app.services.providers import FlightProvider
from src.app.services.refdata import Country
from src.app.services.selection import (
    deal_score,
    favorite_destinations,
    freshness_multiplier,
    select_gems,
)

logger = logging.getLogger(__name__)

# Per stopover tier and city (the provider dedups per city), so this covers
# every destination city of a country with headroom to spare.
CANDIDATES_PER_COUNTRY = 30

# Next-best candidates kept per searched country, so the AI reasoning line
# can say what the winner beat.
RUNNER_UP_COUNT = 2


class DigestResult(BaseModel):
    """Deals across all searched countries, best score first."""

    deals: list[RankedDeal]
    window_start: date
    window_end: date


def build_digest(
    subscriber: Subscriber,
    provider: FlightProvider,
    destinations: list[Country],
    history: SentHistory,
    rng: random.Random | None = None,
    today: date | None = None,
) -> DigestResult:
    start = today or date.today()
    window_start = start + timedelta(days=subscriber.min_days_ahead)
    window_end = start + timedelta(days=subscriber.max_days_ahead)

    def search(origin_iata: str, country: Country) -> list[FlightDeal]:
        query = SearchQuery(
            origin_iata=origin_iata,
            destination_iata=country.code,
            date_from=window_start,
            date_to=window_end,
            min_nights=subscriber.min_nights,
            max_nights=subscriber.max_nights,
            currency=subscriber.currency,
        )
        return [
            deal
            for deal in provider.search_top(query, CANDIDATES_PER_COUNTRY)
            # A candidate's destination can be one of the subscriber's own
            # departure cities (e.g. searching Germany from Frankfurt returns
            # Frankfurt itself, or Berlin for a FRA+BER subscriber); skip those.
            if deal.departure_city != deal.arrival_city
            and deal.arrival_iata not in subscriber.departure_airports
        ]

    def best_pick(country: Country, source: DealSource) -> RankedDeal | None:
        """The country's best-scoring candidate across every departure airport,
        carrying its beaten runner-ups."""
        ranked = sorted(
            (
                RankedDeal(
                    deal=deal,
                    source=source,
                    # The freshness multiplier steers repeating countries
                    # toward fresh cities and sinks repeats in the ranking.
                    score=deal_score(deal) * freshness_multiplier(deal, history),
                    origin_iata=origin_iata,
                )
                for origin_iata in subscriber.departure_airports
                for deal in search(origin_iata, country)
            ),
            key=lambda pick: pick.score,
        )
        if not ranked:
            return None
        winner = ranked[0]
        winner.runner_ups = ranked[1 : 1 + RUNNER_UP_COUNT]
        # Only meaningful once some history exists: a brand-new subscriber's
        # first digest would otherwise badge every single card.
        winner.first_time = (
            bool(history.all_countries)
            and winner.deal.arrival_country not in history.all_countries
        )
        return winner

    favorites = set(subscriber.favorites)
    gems = select_gems(
        destinations,
        favorites,
        set(subscriber.excluded),
        recent=history.recent_countries,
        rng=rng,
    )
    deals = [
        pick
        for country in favorite_destinations(destinations, favorites)
        if (pick := best_pick(country, "favorite"))
    ] + [pick for country in gems if (pick := best_pick(country, "discovery"))]
    deals.sort(key=lambda pick: pick.score)
    logger.info("digest for %s: %d deals", subscriber.email, len(deals))
    return DigestResult(deals=deals, window_start=window_start, window_end=window_end)
