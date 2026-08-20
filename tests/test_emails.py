import random
from typing import Literal

from src.app.models.flights import FlightDeal
from src.app.services.digest import RankedDeal
from src.app.services.emails import FALLBACK_IMAGE, render_digest
from tests.conftest import deal

IMAGES = {"Finland": ["https://img.example/fi.jpg"]}


def ranked(
    flight_deal: FlightDeal, source: Literal["favorite", "discovery"] = "favorite"
) -> RankedDeal:
    return RankedDeal(deal=flight_deal, source=source)


def render(deals: list[RankedDeal]) -> str:
    return render_digest(
        username="Timon",
        update_token="upd123",
        unsubscribe_token="unsub123",
        deals=deals,
        images=IMAGES,
        base_url="https://example.test",
        rng=random.Random(1),
    )


def test_renders_deals() -> None:
    html = render([ranked(deal())])
    assert "Hi Timon!" in html
    assert "129 EUR" in html  # int(), no decimals
    assert "03.09.2026 - 08.09.2026" in html
    assert "https://img.example/fi.jpg" in html
    assert "{{" not in html and "{%" not in html


def test_quality_facts_line_for_direct_flight() -> None:
    html = render([ranked(deal())])
    assert "direct &middot; 2h35 &middot; dep 10:40" in html


def test_quality_facts_line_for_stopover_flight() -> None:
    html = render([ranked(deal(stopovers=1, via_city="Riga", duration_minutes=310))])
    assert "1 stop via Riga &middot; 5h10 &middot; dep 10:40" in html


def test_missing_or_empty_image_lists_fall_back() -> None:
    html = render(
        [ranked(deal(arrival_city="Palma", arrival_country="Spain"), "discovery")]
    )
    assert FALLBACK_IMAGE in html


def test_empty_digest_renders_no_flights_found() -> None:
    html = render([])
    assert html.count("No flights found") == 1


def test_profile_links_use_base_url_and_action_tokens() -> None:
    html = render([])
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
