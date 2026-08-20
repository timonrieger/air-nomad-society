import random
from datetime import datetime

from src.app.services.refdata import Country
from src.app.services.selection import deal_score, favorite_destinations, select_gems
from tests.conftest import deal

DESTINATIONS = [
    Country(country="Finland", code="FI"),
    Country(country="Spain", code="ES"),
    Country(country="Japan", code="JP"),
    Country(country="Brazil", code="BR"),
    Country(country="Canada", code="CA"),
    Country(country="Kenya", code="KE"),
    Country(country="Norway", code="NO"),
]


def test_score_penalizes_stopovers_duration_and_red_eyes() -> None:
    base = deal(price=100)
    assert deal_score(deal(price=100, via_cities=["Riga"])) > deal_score(base)
    assert deal_score(deal(price=100, return_via_cities=["Oslo"])) > deal_score(base)
    assert deal_score(deal(price=100, duration_minutes=600)) > deal_score(base)
    red_eye = deal(price=100, departs_at=datetime(2026, 9, 3, 5, 30))
    assert deal_score(red_eye) > deal_score(base)


def test_quality_beats_small_savings_but_not_big_ones() -> None:
    direct = deal(price=110)
    assert deal_score(deal(price=100, via_cities=["Riga"])) > deal_score(direct)
    assert deal_score(deal(price=60, via_cities=["Riga"])) < deal_score(direct)


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
