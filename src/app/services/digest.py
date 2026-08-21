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

# Next-best candidates kept per searched country, so the AI reasoning line
# can say what the winner beat.
RUNNER_UP_COUNT = 2


class DigestResult(BaseModel):
    """Deals across all searched countries, best score first."""

    deals: list[RankedDeal]
    # The beaten candidates per winning deal, keyed by the winner's
    # arrival_iata, best score first.
    runner_ups: dict[str, list[RankedDeal]]
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

    def top_picks(country: Country, source: DealSource) -> list[RankedDeal]:
        """The country's best-scoring candidates: winner first, then runner-ups."""
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
        ranked = sorted(
            (
                RankedDeal(deal=deal, source=source, score=deal_score(deal))
                for deal in candidates
            ),
            key=lambda pick: pick.score,
        )
        return ranked[: 1 + RUNNER_UP_COUNT]

    favorites = set(subscriber.favorites)
    gems = select_gems(destinations, favorites, set(subscriber.excluded), rng=rng)
    searches: list[tuple[Country, DealSource]] = [
        (country, "favorite")
        for country in favorite_destinations(destinations, favorites)
    ] + [(country, "discovery") for country in gems]
    deals: list[RankedDeal] = []
    runner_ups: dict[str, list[RankedDeal]] = {}
    for country, source in searches:
        picks = top_picks(country, source)
        if picks:
            deals.append(picks[0])
            runner_ups[picks[0].deal.arrival_iata] = picks[1:]
    deals.sort(key=lambda pick: pick.score)
    logger.info("digest for %s: %d deals", subscriber.email, len(deals))
    return DigestResult(
        deals=deals,
        runner_ups=runner_ups,
        window_start=window_start,
        window_end=window_end,
    )
