import random
from datetime import date

from ans.emails import FALLBACK_IMAGE, render_digest
from ans.models import FlightDeal


def deal(arrival_city: str, country: str, price: float) -> FlightDeal:
    return FlightDeal(
        price=price,
        currency="EUR",
        departure_city="Frankfurt",
        departure_iata="FRA",
        arrival_city=arrival_city,
        arrival_iata="XXX",
        arrival_country=country,
        departs_on=date(2026, 9, 3),
        returns_on=date(2026, 9, 8),
        link=f"https://kiwi.com/{arrival_city}?a=1&b=2",
    )


IMAGES = {"Finland": ["https://img.example/fi.jpg"]}


def render(dreams: list[FlightDeal], gems: list[FlightDeal]) -> str:
    return render_digest(
        username="Timon",
        token="tok123",
        dream_deals=dreams,
        gem_deals=gems,
        images=IMAGES,
        base_url="https://example.test",
        rng=random.Random(1),
    )


def test_renders_deals_with_legacy_formatting() -> None:
    html = render([deal("Helsinki", "Finland", 129.99)], [])
    assert "Hi Timon!" in html
    assert ">129 EUR</strong>" in html  # int(), like the legacy f-string
    assert "03.09.2026 - 08.09.2026" in html
    assert "https://img.example/fi.jpg" in html
    assert "{{" not in html and "{%" not in html


def test_missing_or_empty_image_lists_fall_back() -> None:
    html = render([], [deal("Palma", "Spain", 49)])
    assert FALLBACK_IMAGE in html


def test_empty_sections_render_no_flights_found() -> None:
    html = render([], [])
    assert html.count("No Flights") == 2


def test_profile_links_use_base_url_and_token() -> None:
    html = render([], [])
    assert "https://example.test/subscribe?token=tok123" in html
    assert "https://example.test/unsubscribe?token=tok123" in html
    assert "ans.timonrieger.de/subscribe" not in html


def test_alternating_layout_rows() -> None:
    dreams = [deal("Helsinki", "Finland", 100), deal("Tokyo", "Japan", 500)]
    html = render(dreams, [])
    assert 'class="row row-3"' in html  # even index layout
    assert 'class="row row-4"' in html  # odd index layout
