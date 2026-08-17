import random

from ans.refdata import Country
from ans.selection import favorite_destinations, select_gems

DESTINATIONS = [
    Country(country="Finland", code="FI"),
    Country(country="Spain", code="ES"),
    Country(country="Japan", code="JP"),
    Country(country="Brazil", code="BR"),
    Country(country="Canada", code="CA"),
    Country(country="Kenya", code="KE"),
    Country(country="Norway", code="NO"),
]


def test_gems_exclude_favorites_and_excluded_countries() -> None:
    rng = random.Random(42)
    for _ in range(50):
        gems = select_gems(
            DESTINATIONS,
            favorites={"Finland", "Japan"},
            excluded={"Brazil"},
            count=3,
            rng=rng,
        )
        names = {gem.country for gem in gems}
        assert len(gems) == 3
        assert names.isdisjoint({"Finland", "Japan", "Brazil"})


def test_gems_are_unique_and_capped_by_pool_size() -> None:
    gems = select_gems(
        DESTINATIONS,
        favorites={"Finland", "Spain", "Japan", "Brazil"},
        excluded={"Canada", "Kenya"},
        count=5,
        rng=random.Random(1),
    )
    assert [gem.country for gem in gems] == ["Norway"]


def test_favorite_destinations_keeps_reference_order() -> None:
    favorites = favorite_destinations(DESTINATIONS, {"Canada", "Spain"})
    assert [d.country for d in favorites] == ["Spain", "Canada"]
