import random

from markupsafe import escape

from src.models.flights import DealSource, FlightDeal, RankedDeal
from src.services.digest import DigestResult
from src.services.emails import render_digest
from src.services.refdata import FALLBACK_IMAGE
from tests.conftest import deal

IMAGES = {"Finland": ["https://img.example/fi.jpg"]}


def ranked(
    flight_deal: FlightDeal,
    source: DealSource = "favorite",
    reason: str | None = None,
) -> RankedDeal:
    return RankedDeal(
        deal=flight_deal, source=source, score=0.0, reason=reason, origin_iata="FRA"
    )


def render(
    deals: list[RankedDeal],
    baselines: dict[tuple[str, str], float] | None = None,
    username: str = "Timon",
) -> str:
    return render_digest(
        username=username,
        update_token="upd123",
        unsubscribe_token="unsub123",
        digest=DigestResult(deals=deals, baselines=baselines or {}),
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


def test_anchor_line_with_savings_and_exceptional_badge() -> None:
    # 129 vs a 310 median: −58%, comfortably past the 40% tier.
    html = render([ranked(deal())], baselines={("FRA", "HEL"): 310.0})
    assert "typically ~310 EUR (−58%)" in html
    assert "🔥 exceptional price" in html


def test_anchor_line_with_great_badge() -> None:
    # 129 vs 180: −28%, past the 25% tier but short of 40%.
    html = render([ranked(deal())], baselines={("FRA", "HEL"): 180.0})
    assert "typically ~180 EUR (−28%)" in html
    assert "💸 great price" in html
    assert "🔥" not in html


def test_anchor_line_below_tiers_has_no_badge() -> None:
    html = render([ranked(deal())], baselines={("FRA", "HEL"): 140.0})
    assert "typically ~140 EUR (−7%)" in html
    assert "🔥" not in html and "💸" not in html


def test_anchor_line_at_typical_price_shows_no_savings() -> None:
    # 129 vs a 120 median: pricier than typical, no percent bragging.
    html = render([ranked(deal())], baselines={("FRA", "HEL"): 120.0})
    assert "typically ~120 EUR" in html
    assert "(−" not in html


def test_no_anchor_without_baseline() -> None:
    html = render([ranked(deal())])
    assert "typically" not in html


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
