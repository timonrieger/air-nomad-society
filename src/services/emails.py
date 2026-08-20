"""Renders the digest email in memory.

The legacy notification manager appended HTML to a shared file on disk
(templates/send_email.html), sent it, then truncated it — which interleaved
concurrent sends and left stale content behind after a crash. Rendering to a
string removes that state entirely.
"""

import random
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.models.flights import FlightDeal

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
FALLBACK_IMAGE = (
    "https://images.unsplash.com/photo-1500835556837-99ac94a94552?w=800&auto=format"
    "&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8VFJBVkVMfGVufDB8fDB8fHww"
)

# The template is converted 1:1 from the legacy f-strings, which never
# escaped anything; autoescape stays off to keep the output identical.
# Revisit when usernames become untrusted input in Phase 1.
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)  # noqa: S701 # nosec B701


def _present(
    deal: FlightDeal, images: dict[str, list[str]], rng: random.Random
) -> dict[str, Any]:
    country_images = images.get(deal.arrival_country)
    return {
        "price": int(deal.price),
        "currency": deal.currency,
        "dep_city": deal.departure_city,
        "arr_city": deal.arrival_city,
        "arr_country": deal.arrival_country,
        "from_dt": deal.departs_on.strftime("%d.%m.%Y"),
        "to_dt": deal.returns_on.strftime("%d.%m.%Y"),
        "link": deal.link,
        "image_url": rng.choice(country_images) if country_images else FALLBACK_IMAGE,
    }


def render_digest(
    username: str,
    token: str,
    dream_deals: list[FlightDeal],
    gem_deals: list[FlightDeal],
    images: dict[str, list[str]],
    base_url: str,
    rng: random.Random | None = None,
) -> str:
    picker = rng or random.Random()  # nosec B311 # picks photos, not secrets
    return _env.get_template("digest.html.j2").render(
        username=username,
        token=token,
        dream_flights=[_present(deal, images, picker) for deal in dream_deals],
        gem_flights=[_present(deal, images, picker) for deal in gem_deals],
        base_url=base_url,
    )
