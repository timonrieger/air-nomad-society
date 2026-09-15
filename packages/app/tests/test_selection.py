import random
from datetime import datetime

from src.models.flights import LowClaim
from src.models.history import SentHistory
from src.services.refdata import Country
from src.services.selection import (
    deal_score,
    freshness_multiplier,
    low_badge,
    price_low_since,
    select_gems,
)
from tests.conftest import deal, price_series

DESTINATIONS = [
    Country(country="Finland", code="FI", region="Europe"),
    Country(country="Spain", code="ES", region="Europe"),
    Country(country="Japan", code="JP", region="Asia"),
    Country(country="Brazil", code="BR", region="South America"),
    Country(country="Canada", code="CA", region="North America"),
    Country(country="Kenya", code="KE", region="Africa"),
    Country(country="Norway", code="NO", region="Europe"),
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
    assert freshness_multiplier(deal(), "discovery", SentHistory(), None) == 1.0


def test_recent_country_penalty_and_long_low_waiver() -> None:
    history = SentHistory(recent_countries={"Finland"})
    week_low = LowClaim(since=datetime(2026, 8, 25), weeks=1)
    assert freshness_multiplier(deal(), "discovery", history, week_low) == 1.25
    # A fare that has been the route's low for two months repeats freely.
    long_low = LowClaim(since=datetime(2026, 7, 1), weeks=8)
    assert freshness_multiplier(deal(), "discovery", history, long_low) == 1.0


def test_favorites_are_exempt_from_the_country_penalty() -> None:
    # Favorites are re-sent weekly by contract; only repeating a city costs.
    history = SentHistory(recent_countries={"Finland"})
    assert freshness_multiplier(deal(price=999), "favorite", history, None) == 1.0
    history.recent_cities.add("HEL")
    assert freshness_multiplier(deal(price=999), "favorite", history, None) == 1.15


def test_waiver_clears_the_city_penalty_too() -> None:
    # A long-standing low recurs in the same city; that is the point of it.
    history = SentHistory(recent_countries={"Finland"}, recent_cities={"HEL"})
    long_low = LowClaim(since=datetime(2026, 7, 1), weeks=9)
    assert freshness_multiplier(deal(), "discovery", history, long_low) == 1.0


def test_recent_country_without_a_claim_is_always_penalized() -> None:
    history = SentHistory(recent_countries={"Finland"})
    assert freshness_multiplier(deal(price=1), "discovery", history, None) == 1.25


def test_recent_city_penalty_stacks_on_country() -> None:
    history = SentHistory(recent_countries={"Finland"}, recent_cities={"HEL"})
    assert (
        freshness_multiplier(deal(price=999), "discovery", history, None) == 1.25 * 1.15
    )
    fresh_city = deal(price=999, arrival_iata="TKU")
    assert freshness_multiplier(fresh_city, "discovery", history, None) == 1.25


BEFORE = datetime(2026, 9, 1)
JUNE = datetime(2026, 6, 1)


def test_low_since_needs_enough_distinct_days() -> None:
    assert price_low_since(price_series(200, 300, 400, start=JUNE), 100, BEFORE) is None
    # Four prices on one day are a snapshot, not history.
    same_day = [(datetime(2026, 6, 1, hour), 200.0) for hour in (6, 9, 12, 15)]
    assert price_low_since(same_day, 100, BEFORE) is None


def test_matching_an_old_price_breaks_the_streak() -> None:
    observations = price_series(200, 150, 130, 180, start=JUNE)
    claim = price_low_since(observations, 130, BEFORE)
    # The equal fare on Jun 3 ends the streak there: flat fares claim little.
    assert claim == LowClaim(since=datetime(2026, 6, 3), weeks=12)


def test_undercutting_everything_claims_the_full_data_span() -> None:
    claim = price_low_since(
        price_series(200, 150, 130, 180, start=JUNE), 129.99, BEFORE
    )
    assert claim == LowClaim(since=JUNE, weeks=13)


def test_streaks_below_the_lowest_tier_are_no_claim() -> None:
    # An equal price nine days ago caps the streak at one week: not a claim.
    recent = price_series(200, 150, 130, 100, start=datetime(2026, 8, 20))
    assert price_low_since(recent, 100, BEFORE) is None


def test_observations_at_or_after_before_are_ignored() -> None:
    # The run's own morning and anything later never anchor a claim.
    observations = price_series(200, 210, 220, 230, start=JUNE) + [
        (BEFORE, 50.0),
        (datetime(2026, 9, 2), 50.0),
    ]
    claim = price_low_since(observations, 100, BEFORE)
    assert claim == LowClaim(since=JUNE, weeks=13)


def test_low_badges_by_streak_length() -> None:
    assert low_badge(30) == "🔥 lowest in 6 months"
    assert low_badge(8) == "💸 lowest in 2 months"
    assert low_badge(4) == "📉 lowest in a month"
    assert low_badge(3) is None
