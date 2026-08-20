"""Destination selection for the digest."""

import random
from collections.abc import Sequence

from src.app.services.refdata import Country

GEM_COUNT = 5


def select_gems(
    destinations: Sequence[Country],
    favorites: set[str],
    excluded: set[str],
    count: int = GEM_COUNT,
    rng: random.Random | None = None,
) -> list[Country]:
    """Pick random "secret gem" countries for a subscriber.

    Gems never overlap with the subscriber's favorite countries (those get
    their own section) or the countries they excluded. The legacy loop in
    main.py tried the same thing but broke out of the wrong loop, so all but
    the first collision with a favorite slipped through.
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
