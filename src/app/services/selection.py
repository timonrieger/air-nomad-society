"""Destination selection and deal scoring for the digest."""

import random
from collections.abc import Sequence

from src.app.models.flights import FlightDeal
from src.app.services.refdata import Country

GEM_COUNT = 5

# Comfort penalties expressed as fare fractions, so the score stays
# currency-agnostic: a stopover "costs" 25% of the ticket, every outbound
# hour 2%, and a red-eye departure 15%.
STOPOVER_PENALTY = 0.25
HOURLY_PENALTY = 0.02
RED_EYE_PENALTY = 0.15
DAYTIME_HOURS = range(7, 21)


def deal_score(deal: FlightDeal) -> float:
    """Effective price of a deal — the fare inflated by comfort penalties.

    Lower is better. Deterministic on purpose: it is the baseline any future
    AI judge gets compared against.
    """
    penalty = (
        1.0
        + STOPOVER_PENALTY * len(deal.via_cities)
        + HOURLY_PENALTY * deal.duration_minutes / 60
    )
    if deal.departs_at.hour not in DAYTIME_HOURS:
        penalty += RED_EYE_PENALTY
    return deal.price * penalty


def select_gems(
    destinations: Sequence[Country],
    favorites: set[str],
    excluded: set[str],
    count: int = GEM_COUNT,
    rng: random.Random | None = None,
) -> list[Country]:
    """Pick random "secret gem" countries for a subscriber.

    Gems never overlap with the subscriber's favorite countries (those are
    always searched) or the countries they excluded.
    """
    pool = [
        destination
        for destination in destinations
        if destination.country not in favorites and destination.country not in excluded
    ]
    picker = rng or random
    return picker.sample(pool, min(count, len(pool)))


def favorite_destinations(
    destinations: Sequence[Country], favorites: set[str]
) -> list[Country]:
    """The subscriber's favorite countries, in reference-data order."""
    return [d for d in destinations if d.country in favorites]
