import random

from src.app.services.emails import FALLBACK_IMAGE, render_digest
from src.app.models.flights import FlightDeal
from tests.conftest import deal

IMAGES = {"Finland": ["https://img.example/fi.jpg"]}


def render(dreams: list[FlightDeal], gems: list[FlightDeal]) -> str:
    return render_digest(
        username="Timon",
        update_token="upd123",
        unsubscribe_token="unsub123",
        dream_deals=dreams,
        gem_deals=gems,
        images=IMAGES,
        base_url="https://example.test",
        rng=random.Random(1),
    )


def test_renders_deals() -> None:
    html = render([deal()], [])
    assert "Hi Timon!" in html
    assert "129 EUR" in html  # int(), no decimals
    assert "03.09.2026 - 08.09.2026" in html
    assert "https://img.example/fi.jpg" in html
    assert "{{" not in html and "{%" not in html


def test_missing_or_empty_image_lists_fall_back() -> None:
    html = render([], [deal(arrival_city="Palma", arrival_country="Spain")])
    # Autoescape turns the URL's "&" into "&amp;", so match its unique photo id.
    assert "photo-1500835556837" in html
    assert "photo-1500835556837" in FALLBACK_IMAGE


def test_empty_sections_render_no_flights_found() -> None:
    html = render([], [])
    assert html.count("No flights found") == 2


def test_username_html_is_escaped() -> None:
    html = render_digest(
        username="<a href=//evil.co>x",
        update_token="upd123",
        unsubscribe_token="unsub123",
        dream_deals=[],
        gem_deals=[],
        images=IMAGES,
        base_url="https://example.test",
    )
    assert "<a href=//evil.co>" not in html
    assert "&lt;a href=//evil.co&gt;x" in html


def test_profile_links_use_base_url_and_action_tokens() -> None:
    html = render([], [])
    assert "https://example.test/subscribe?token=upd123" in html
    assert "https://example.test/unsubscribe?token=unsub123" in html
    assert "ans.timonrieger.de/subscribe" not in html


def test_renders_a_card_per_deal() -> None:
    dreams = [deal(), deal(arrival_city="Tokyo", arrival_country="Japan")]
    html = render(dreams, [])
    assert "Frankfurt &ndash; Helsinki" in html
    assert "Frankfurt &ndash; Tokyo" in html
    assert html.count("Book Now") == 2
