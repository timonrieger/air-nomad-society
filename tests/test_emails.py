import random
from datetime import date

import pytest

from src.app.models.flights import DealSource, FlightDeal, RankedDeal
from src.app.services.digest import DigestResult
from src.app.services.emails import FALLBACK_IMAGE, render_digest
from tests.conftest import deal

IMAGES = {"Finland": ["https://img.example/fi.jpg"]}


def ranked(flight_deal: FlightDeal, source: DealSource = "favorite") -> RankedDeal:
    return RankedDeal(deal=flight_deal, source=source, score=0.0)


def render(
    deals: list[RankedDeal],
    window_start: date = date(2026, 9, 1),
    window_end: date = date(2026, 9, 30),
) -> str:
    return render_digest(
        username="Timon",
        update_token="upd123",
        unsubscribe_token="unsub123",
        digest=DigestResult(
            deals=deals, window_start=window_start, window_end=window_end
        ),
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


def test_date_window_framing() -> None:
    html = render([ranked(deal())])
    assert "depart Sep 1–30 · e.g. 03.09–08.09" in html


def test_date_window_crossing_months_names_both() -> None:
    html = render(
        [ranked(deal())],
        window_start=date(2026, 9, 26),
        window_end=date(2026, 10, 12),
    )
    assert "depart Sep 26 – Oct 12" in html


def test_date_window_crossing_years_names_both_years() -> None:
    html = render(
        [ranked(deal())],
        window_start=date(2026, 12, 15),
        window_end=date(2027, 1, 20),
    )
    assert "depart Dec 15, 2026 – Jan 20, 2027" in html


def test_empty_digest_refuses_to_render() -> None:
    with pytest.raises(AssertionError):
        render([])


def test_provenance_badges() -> None:
    assert "⭐ favorite" in render([ranked(deal())])
    assert "✨ discovery" in render([ranked(deal(), "discovery")])


def test_quality_facts_line_for_direct_flight() -> None:
    html = render([ranked(deal())])
    assert "direct · 2h35 · dep 10:40" in html


def test_quality_facts_line_for_stopover_flight() -> None:
    html = render([ranked(deal(via_cities=["Riga"], duration_minutes=310))])
    assert "1 stop via Riga · 5h10 · dep 10:40" in html


def test_quality_facts_line_counts_return_stopovers() -> None:
    html = render([ranked(deal(via_cities=["Riga"], return_via_cities=["Oslo"]))])
    assert "2 stops via Riga, Oslo" in html


def test_notice_when_favorites_yield_nothing() -> None:
    notice = "Your favorite countries came up empty"
    assert notice in render([ranked(deal(), "discovery")])
    assert notice not in render([ranked(deal(), "favorite")])


def test_missing_or_empty_image_lists_fall_back() -> None:
    html = render(
        [ranked(deal(arrival_city="Palma", arrival_country="Spain"), "discovery")]
    )
    assert FALLBACK_IMAGE in html


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
