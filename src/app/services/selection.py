"""Destination selection and deal scoring for the digest."""

import random
from collections.abc import Sequence

from src.app.models.flights import DealSource, FlightDeal
from src.app.models.history import SentHistory
from src.app.services.refdata import Country

GEM_COUNT = 5

# Comfort penalties expressed as fare fractions, so the score stays
# currency-agnostic: a stopover "costs" 25% of the ticket, every outbound
# hour 2%, and a red-eye departure 15%.
STOPOVER_PENALTY = 0.25
HOURLY_PENALTY = 0.02
RED_EYE_PENALTY = 0.15
DAYTIME_HOURS = range(7, 21)

# Repetition penalties — country first, then city — and the price cut that
# lets a favorite repeat anyway.
COUNTRY_REPEAT_PENALTY = 1.25
CITY_REPEAT_PENALTY = 1.15
CLEARLY_BETTER_FRACTION = 0.85


def deal_score(deal: FlightDeal) -> float:
    """Effective price of a deal — the fare inflated by comfort penalties.

    Lower is better. Deterministic on purpose: it is the baseline any future
    AI judge gets compared against.
    """
    penalty = (
        1.0
        + STOPOVER_PENALTY * deal.stopovers
        + HOURLY_PENALTY * deal.duration_minutes / 60
    )
    if deal.departs_at.hour not in DAYTIME_HOURS:
        penalty += RED_EYE_PENALTY
    return deal.price * penalty


def freshness_multiplier(
    deal: FlightDeal, source: DealSource, history: SentHistory
) -> float:
    """Score inflation for repetition — the top churn driver of deal digests.

    Country first, then city: a recently-sent country costs 25%, and a
    recently-sent city another 15% on top, so a repeating country rotates
    its cities. Favorites are exempt from the country penalty — they are
    re-sent every week by contract, so it would apply to them permanently
    and just handicap them against gems — but still pay for repeating a
    city. A fare clearly below the cheapest recently sent one there (≥15%
    cheaper) repeats with no penalty at all — that price drop is exactly
    what is worth resending."""
    if deal.arrival_country not in history.recent_countries:
        return 1.0
    best = history.recent_country_prices.get(deal.arrival_country)
    # Rounded to cents so 0.85 × best can't float-drift just below an
    # exactly-15%-cheaper fare.
    if best is not None and deal.price <= round(CLEARLY_BETTER_FRACTION * best, 2):
        return 1.0
    multiplier = 1.0 if source == "favorite" else COUNTRY_REPEAT_PENALTY
    if deal.arrival_iata in history.recent_cities:
        multiplier *= CITY_REPEAT_PENALTY
    return multiplier


def select_gems(
    destinations: Sequence[Country],
    favorites: set[str],
    excluded: set[str],
    recent: set[str],
    count: int = GEM_COUNT,
    rng: random.Random | None = None,
) -> list[Country]:
    """Pick random "secret gem" countries for a subscriber.

    Gems never overlap with the subscriber's favorite countries (those are
    always searched) or the countries they excluded, and prefer countries
    not recently sent — topping up from recently-sent ones only when the
    fresh pool runs short.
    """
    pool = [
        destination
        for destination in destinations
        if destination.country not in favorites and destination.country not in excluded
    ]
    fresh = [destination for destination in pool if destination.country not in recent]
    stale = [destination for destination in pool if destination.country in recent]
    picker = rng or random
    picked = picker.sample(fresh, min(count, len(fresh)))
    picked += picker.sample(stale, min(count - len(picked), len(stale)))
    return picked


def favorite_destinations(
    destinations: Sequence[Country], favorites: set[str]
) -> list[Country]:
    """The subscriber's favorite countries, in reference-data order."""
    return [d for d in destinations if d.country in favorites]
