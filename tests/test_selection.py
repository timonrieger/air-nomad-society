import random
from datetime import datetime

from src.app.services.history import SentHistory
from src.app.services.refdata import Country
from src.app.services.selection import (
    deal_score,
    favorite_destinations,
    freshness_multiplier,
    select_gems,
)
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
            recent=set(),
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
        recent=set(),
        count=5,
        rng=random.Random(1),
    )
    assert [gem.country for gem in gems] == ["Norway"]


def test_gems_prefer_countries_not_recently_sent() -> None:
    rng = random.Random(7)
    recent = {"Spain", "Brazil", "Canada", "Kenya"}
    for _ in range(50):
        gems = select_gems(DESTINATIONS, set(), set(), recent=recent, count=3, rng=rng)
        # Three fresh countries exist, so no recently-sent one is picked.
        assert {gem.country for gem in gems} == {"Finland", "Japan", "Norway"}


def test_gems_top_up_from_recent_when_fresh_pool_runs_short() -> None:
    recent = {d.country for d in DESTINATIONS} - {"Norway"}
    gems = select_gems(
        DESTINATIONS, set(), set(), recent=recent, count=3, rng=random.Random(1)
    )
    assert len(gems) == 3
    assert "Norway" in {gem.country for gem in gems}


def test_fresh_deal_is_not_penalized() -> None:
    assert freshness_multiplier(deal(), SentHistory()) == 1.0


def test_recent_country_penalty_and_clearly_better_waiver() -> None:
    history = SentHistory(
        recent_countries={"Finland"}, recent_country_prices={"Finland": 150.0}
    )
    assert freshness_multiplier(deal(price=140), history) == 1.25
    # ≥15% below the cheapest recently sent price repeats without penalty.
    assert freshness_multiplier(deal(price=127), history) == 1.0


def test_recent_country_without_comparable_price_is_always_penalized() -> None:
    history = SentHistory(recent_countries={"Finland"})
    assert freshness_multiplier(deal(price=1), history) == 1.25


def test_recent_city_penalty_stacks_on_country() -> None:
    history = SentHistory(recent_countries={"Finland"}, recent_cities={"HEL"})
    assert freshness_multiplier(deal(price=999), history) == 1.25 * 1.15
    fresh_city = deal(price=999, arrival_iata="TKU")
    assert freshness_multiplier(fresh_city, history) == 1.25


def test_favorite_destinations_keeps_reference_order() -> None:
    favorites = favorite_destinations(DESTINATIONS, {"Canada", "Spain"})
    assert [d.country for d in favorites] == ["Spain", "Canada"]
