"""Builds one subscriber's digest: the best-scoring deal per searched country
(favorites plus randomly picked "secret gem" countries), ranked into one list."""

import logging
import random
from collections.abc import Callable
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

# Typical price per (origin, arrival) route — history.route_baselines bound
# to the subscriber's currency and the run boundary by the caller.
BaselineLookup = Callable[[set[tuple[str, str]]], dict[tuple[str, str], float]]


class DigestResult(BaseModel):
    """Deals across all searched countries, best score first."""

    deals: list[RankedDeal]
    # Typical price per searched route: selection consulted these for the
    # repeat waiver, and rendering reuses them for the anchor line.
    baselines: dict[tuple[str, str], float]
    window_start: date
    window_end: date

    def baseline_for(self, ranked: RankedDeal) -> float | None:
        """The typical price of the route this pick was searched on."""
        return self.baselines.get((ranked.origin_iata, ranked.deal.arrival_iata))


def build_digest(
    subscriber: Subscriber,
    provider: FlightProvider,
    destinations: list[Country],
    history: SentHistory,
    baselines_for: BaselineLookup,
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

    def best_pick(
        source: DealSource,
        candidates: list[tuple[str, FlightDeal]],
        baselines: dict[tuple[str, str], float],
    ) -> RankedDeal | None:
        """One country's best-scoring candidate across every departure
        airport, carrying its beaten runner-ups."""
        ranked = sorted(
            (
                RankedDeal(
                    deal=deal,
                    source=source,
                    # The freshness multiplier steers repeating countries
                    # toward fresh cities and sinks repeats in the ranking.
                    score=deal_score(deal)
                    * freshness_multiplier(
                        deal,
                        source,
                        history,
                        baselines.get((origin_iata, deal.arrival_iata)),
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
    searches: list[tuple[DealSource, Country]] = [
        ("favorite", country)
        for country in favorite_destinations(destinations, favorites)
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
    # Baselines feed two things: the repeat waiver — which only candidates in
    # recently-sent countries can consult — and the winners' anchor lines.
    # Fetch the waiver-eligible routes, rank, then top up whatever winning
    # routes that fetch didn't cover, so history growth never drags the whole
    # candidate cross-product into every run.
    eligible = {
        (origin_iata, deal.arrival_iata)
        for _, candidates in found
        for origin_iata, deal in candidates
        if deal.arrival_country in history.recent_countries
    }
    baselines = baselines_for(eligible) if eligible else {}
    deals = [
        pick
        for source, candidates in found
        if (pick := best_pick(source, candidates, baselines))
    ]
    deals.sort(key=lambda pick: pick.score)
    winner_routes = {(pick.origin_iata, pick.deal.arrival_iata) for pick in deals}
    if missing := winner_routes - eligible:
        baselines |= baselines_for(missing)
    logger.info("digest for %s: %d deals", subscriber.email, len(deals))
    return DigestResult(
        deals=deals,
        baselines=baselines,
        window_start=window_start,
        window_end=window_end,
    )
