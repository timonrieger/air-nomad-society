import random
from datetime import datetime

from markupsafe import escape

from src.models.flights import DealSource, FlightDeal, LowClaim, RankedDeal
from src.services.digest import DigestResult
from src.services.emails import render_digest
from src.services.refdata import FALLBACK_IMAGE
from tests.conftest import deal

IMAGES = {"Finland": ["https://img.example/fi.jpg"]}


def ranked(
    flight_deal: FlightDeal,
    source: DealSource = "favorite",
    reason: str | None = None,
    low: LowClaim | None = None,
) -> RankedDeal:
    return RankedDeal(
        deal=flight_deal,
        source=source,
        score=0.0,
        reason=reason,
        low=low,
        origin_iata="FRA",
    )


def low(weeks: int) -> LowClaim:
    return LowClaim(since=datetime(2026, 6, 12), weeks=weeks)


def render(deals: list[RankedDeal], username: str = "Timon") -> str:
    return render_digest(
        username=username,
        update_token="upd123",
        unsubscribe_token="unsub123",
        digest=DigestResult(deals=deals),
        images=IMAGES,
        base_url="https://example.test",
        rng=random.Random(1),
    )


def test_renders_deals() -> None:
    html = render([ranked(deal())])
    assert "Hi Timon!" in html
    assert "129 EUR" in html  # int(), no decimals
    assert "https://img.example/fi.jpg" in html
    assert "{{" not in html and "{%" not in html


def test_username_markup_is_escaped() -> None:
    html = render([ranked(deal())], username="<b>Nomad</b>")
    assert "<b>Nomad</b>" not in html
    assert "Hi &lt;b&gt;Nomad&lt;/b&gt;!" in html


def test_card_shows_country_and_plain_travel_dates() -> None:
    html = render([ranked(deal())])
    assert "Finland &middot; 03.09–08.09" in html
    assert "depart" not in html


def test_provenance_badges() -> None:
    assert "⭐ favorite" in render([ranked(deal())])
    assert "✨ discovery" in render([ranked(deal(), "discovery")])


def test_anchor_line_and_badge_for_a_six_month_low() -> None:
    html = render([ranked(deal(), low=low(weeks=27))])
    assert "lowest price since Jun 12" in html
    assert "🔥 lowest in 6 months" in html


def test_two_month_low_badge() -> None:
    html = render([ranked(deal(), low=low(weeks=9))])
    assert "lowest price since Jun 12" in html
    assert "💸 lowest in 2 months" in html
    assert "🔥" not in html


def test_one_month_low_badge() -> None:
    html = render([ranked(deal(), low=low(weeks=4))])
    assert "📉 lowest in a month" in html


def test_short_streaks_get_no_anchor_and_no_badge() -> None:
    # Below the lowest tier the claim is not worth a line either.
    html = render([ranked(deal(), low=low(weeks=3))])
    assert "lowest price" not in html
    assert "🔥" not in html and "💸" not in html and "📉" not in html


def test_no_anchor_without_a_claim() -> None:
    html = render([ranked(deal())])
    assert "lowest price" not in html


def test_new_for_you_badge_for_first_time_countries() -> None:
    pick = ranked(deal())
    pick.first_time = True
    assert "✨ new for you" in render([pick])
    assert "✨ new for you" not in render([ranked(deal())])


def test_reason_line_renders_when_present() -> None:
    reason = "Direct at 10:40 — beat a cheaper red-eye with a stop."
    html = render([ranked(deal(), reason=reason)])
    assert reason in html
    assert reason not in render([ranked(deal())])


def test_quality_facts_line_for_direct_flight() -> None:
    html = render([ranked(deal())])
    assert "direct · 2h35 · dep 10:40" in html


def test_quality_facts_line_for_stopover_flight() -> None:
    html = render([ranked(deal(via_cities=["Riga"], duration_minutes=310))])
    assert "with stopover · 5h10 · dep 10:40" in html


def test_missing_or_empty_image_lists_fall_back() -> None:
    html = render(
        [ranked(deal(arrival_city="Palma", arrival_country="Spain"), "discovery")]
    )
    # Autoescape renders the URL's & as &amp; inside the src attribute.
    assert escape(FALLBACK_IMAGE) in html


def test_profile_links_use_base_url_and_action_tokens() -> None:
    html = render([ranked(deal())])
    assert "https://example.test/subscribe?token=upd123" in html
    assert "https://example.test/unsubscribe?token=unsub123" in html
    assert "ans.timonrieger.de/subscribe" not in html


def test_renders_a_card_per_deal() -> None:
    deals = [
        ranked(deal()),
        ranked(deal(arrival_city="Tokyo", arrival_country="Japan"), "discovery"),
    ]
    html = render(deals)
    assert "Frankfurt &ndash; Helsinki" in html
    assert "Frankfurt &ndash; Tokyo" in html
    assert html.count("Book Now") == 2
