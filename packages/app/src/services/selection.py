"""Destination selection, deal scoring, and lowest-price claims for the digest."""

import random
from collections.abc import Sequence
from datetime import datetime

from src.models.flights import DealSource, FlightDeal, LowClaim
from src.models.history import SentHistory
from src.services.refdata import Country

# Comfort penalties expressed as fare fractions
STOPOVER_PENALTY = 0.25
HOURLY_PENALTY = 0.02
RED_EYE_PENALTY = 0.15
DAYTIME_HOURS = range(7, 21)

# Repetition penalties to steer towards varying results
COUNTRY_REPEAT_PENALTY = 1.25
CITY_REPEAT_PENALTY = 1.15

MIN_OBSERVATION_DAYS = 4

# The last tier is the claim floor for both the wall and the email anchor.
LOW_TIERS: list[tuple[int, str]] = [
    (26, "🔥 lowest in 6 months"),
    (8, "💸 lowest in 2 months"),
    (4, "📉 lowest in a month"),
]

WAIVER_MIN_WEEKS = 8

Observation = tuple[datetime, float]


def price_low_since(
    observations: list[Observation], fare_eur: float, before: datetime
) -> LowClaim | None:
    """The lowest-price claim a fare earns on its route.

    Only observations strictly before `before` count (pass the run start or
    the send time, so a claim never anchors on its own run). A fare merely
    matching an old price breaks the streak there — a flat fare never claims
    a low. A fare under everything claims the full data span, so a claim can
    never overstate the history backing it. Streaks shorter than the lowest
    badge tier, or backed by fewer than MIN_OBSERVATION_DAYS distinct days,
    are no claim at all."""
    past = [(at, price) for at, price in observations if at < before]
    if len({at.date() for at, _ in past}) < MIN_OBSERVATION_DAYS:
        return None
    since = max(
        (at for at, price in past if price <= fare_eur),
        default=min(at for at, _ in past),
    )
    weeks = (before - since).days // 7
    return LowClaim(since=since, weeks=weeks) if weeks >= LOW_TIERS[-1][0] else None


def low_badge(weeks: int) -> str | None:
    """The tier badge a streak length earns, if any."""
    return next((label for cut, label in LOW_TIERS if weeks >= cut), None)


def deal_score(deal: FlightDeal) -> float:
    """Effective price of a deal, inflated by comfort penalties. Lower is better. Deterministic."""
    penalty = (
        1.0
        + STOPOVER_PENALTY * deal.stopovers
        + HOURLY_PENALTY * deal.duration_minutes / 60
    )
    if deal.departs_at.hour not in DAYTIME_HOURS:
        penalty += RED_EYE_PENALTY
    return deal.price * penalty


def freshness_multiplier(
    deal: FlightDeal,
    source: DealSource,
    history: SentHistory,
    low: LowClaim | None,
) -> float:
    """Score inflation for repetition.

    A fare that has been its route's low for WAIVER_MIN_WEEKS repeats with
    no penalty at all — a genuine deal is worth resending."""
    if deal.arrival_country not in history.recent_countries:
        return 1.0
    if low is not None and low.weeks >= WAIVER_MIN_WEEKS:
        return 1.0
    # excempt favorites to avoid permanent handicap
    multiplier = 1.0 if source == "favorite" else COUNTRY_REPEAT_PENALTY
    if deal.arrival_iata in history.recent_cities:
        multiplier *= CITY_REPEAT_PENALTY
    return multiplier


def select_gems(
    destinations: Sequence[Country],
    favorites: set[str],
    excluded: set[str],
    recent: set[str],
    count: int,
    rng: random.Random | None = None,
) -> list[Country]:
    """Pick random "secret gem" countries for a subscriber."""
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
