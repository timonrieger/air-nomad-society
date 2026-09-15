"""Builds one subscriber's digest: the best-scoring deal per searched country
(every favorite, plus a fixed number of randomly picked discovery countries
when the subscriber opts into them), ranked into one list."""

import logging
import random
from collections.abc import Callable
from datetime import date, datetime, time, timedelta

from pydantic import BaseModel

from src.models.subscriber import Subscriber
from src.models.flights import DealSource, FlightDeal, RankedDeal, SearchQuery
from src.models.history import SentHistory
from src.services.providers import FlightProvider
from src.services.refdata import Country
from src.services.selection import (
    Observation,
    deal_score,
    freshness_multiplier,
    price_low_since,
    select_gems,
)

logger = logging.getLogger(__name__)

# Per stopover tier and city (the provider dedups per city), so this covers
# every destination city of a country with headroom to spare.
CANDIDATES_PER_COUNTRY = 30

# Next-best candidates kept per searched country, so the AI reasoning line
# can say what the winner beat.
RUNNER_UP_COUNT = 2

# Discoveries carried by a digest that opts into them. Fixed rather than
# per-subscriber: every one is a searched country, so this is a direct
# multiplier on the run's provider budget (#63).
DISCOVERIES_PER_DIGEST = 3

# EUR observations per (origin, arrival) route — history.route_observations
# bound to the run boundary by the caller.
ObservationLookup = Callable[
    [set[tuple[str, str]]], dict[tuple[str, str], list[Observation]]
]


class DigestResult(BaseModel):
    """Deals across all searched countries, best score first."""

    deals: list[RankedDeal]


def build_digest(
    subscriber: Subscriber,
    provider: FlightProvider,
    destinations: list[Country],
    history: SentHistory,
    observations_for: ObservationLookup,
    rng: random.Random | None = None,
    today: date | None = None,
) -> DigestResult:
    start = today or date.today()
    run_start = datetime.combine(start, time.min)
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
            if deal.departure_city != deal.arrival_city
            and deal.arrival_iata not in subscriber.departure_airports
        ]

    def best_pick(
        source: DealSource,
        candidates: list[tuple[str, FlightDeal]],
        observations: dict[tuple[str, str], list[Observation]],
    ) -> RankedDeal | None:
        """One country's best-scoring candidate across every departure
        airport, carrying its beaten runner-ups."""
        ranked = sorted(
            (
                RankedDeal(
                    deal=deal,
                    source=source,
                    score=deal_score(deal)
                    * freshness_multiplier(
                        deal,
                        source,
                        history,
                        price_low_since(
                            observations.get((origin_iata, deal.arrival_iata), []),
                            deal.price_eur,
                            before=run_start,
                        ),
                    ),
                    origin_iata=origin_iata,
                )
                for origin_iata, deal in candidates
            ),
            key=lambda pick: pick.score,
        )
        if not ranked:
            return None
        winner = ranked[0]
        winner.runner_ups = ranked[1 : 1 + RUNNER_UP_COUNT]
        winner.first_time = (
            bool(history.all_countries)
            and winner.deal.arrival_country not in history.all_countries
        )
        return winner

    favorites = set(subscriber.favorites)
    gems = (
        select_gems(
            destinations,
            favorites,
            set(subscriber.excluded),
            recent=history.recent_countries,
            count=DISCOVERIES_PER_DIGEST,
            rng=rng,
        )
        if subscriber.include_discoveries
        else []
    )
    searches: list[tuple[DealSource, Country]] = [
        ("favorite", country)
        for country in [d for d in destinations if d.country in favorites]
    ] + [("discovery", country) for country in gems]
    found = [
        (
            source,
            [
                (origin_iata, deal)
                for origin_iata in subscriber.departure_airports
                for deal in search(origin_iata, country)
            ],
        )
        for source, country in searches
    ]
    # Observations feed two things: the repeat waiver — which only candidates
    # in recently-sent countries can consult — and the winners' lowest-price
    # claims. Fetch the waiver-eligible routes, rank, then top up whatever
    # winning routes that fetch didn't cover, so history growth never drags
    # the whole candidate cross-product into every run.
    eligible = {
        (origin_iata, deal.arrival_iata)
        for _, candidates in found
        for origin_iata, deal in candidates
        if deal.arrival_country in history.recent_countries
    }
    observations = observations_for(eligible) if eligible else {}
    deals = [
        pick
        for source, candidates in found
        if (pick := best_pick(source, candidates, observations))
    ]
    deals.sort(key=lambda pick: pick.score)
    winner_routes = {(pick.origin_iata, pick.deal.arrival_iata) for pick in deals}
    if missing := winner_routes - eligible:
        observations |= observations_for(missing)
    for pick in deals:
        pick.low = price_low_since(
            observations.get((pick.origin_iata, pick.deal.arrival_iata), []),
            pick.deal.price_eur,
            before=run_start,
        )
    logger.info("digest for %s: %d deals", subscriber.email, len(deals))
    return DigestResult(deals=deals)
