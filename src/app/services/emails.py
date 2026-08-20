"""Renders the digest and confirmation emails and owns their subjects and links."""

import json
import random
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.app.config import Settings
from src.app.models.flights import FlightDeal
from src.app.services import mailer
from src.app.services.tokens import issue_token

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

DIGEST_SUBJECT = "Weekly Flight Deals!"
CONFIRM_SUBJECT = "Confirm your subscription"

# The shared brand definition (one accent, one gray scale, one font stack);
# src/web consumes the same file via the brand-theme plugin in vite.config.ts.
# Emails render on white with the light end of the scale, the web on the dark.
TOKENS: dict[str, str] = json.loads(
    (TEMPLATE_DIR.parent / "brand.json").read_text(encoding="utf-8")
)
FALLBACK_IMAGE = (
    "https://images.unsplash.com/photo-1500835556837-99ac94a94552?w=800&auto=format"
    "&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8VFJBVkVMfGVufDB8fDB8fHww"
)

# Usernames come straight from the public subscribe form; autoescape keeps
# them from injecting HTML into the emails we send.
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)


def _present(
    deal: FlightDeal, images: dict[str, list[str]], rng: random.Random
) -> dict[str, Any]:
    country_images = images.get(deal.arrival_country)
    return {
        "deal": deal,
        "image_url": rng.choice(country_images) if country_images else FALLBACK_IMAGE,
    }


def render_digest(
    username: str,
    update_token: str,
    unsubscribe_token: str,
    dream_deals: list[FlightDeal],
    gem_deals: list[FlightDeal],
    images: dict[str, list[str]],
    base_url: str,
    rng: random.Random | None = None,
) -> str:
    picker = rng or random.Random()  # nosec B311 # picks photos, not secrets
    return _env.get_template("digest.html.j2").render(
        t=TOKENS,
        username=username,
        site_url=base_url,
        update_url=f"{base_url}/subscribe?token={update_token}",
        unsubscribe_url=f"{base_url}/unsubscribe?token={unsubscribe_token}",
        dream_flights=[_present(deal, images, picker) for deal in dream_deals],
        gem_flights=[_present(deal, images, picker) for deal in gem_deals],
    )


def render_confirmation(username: str, confirm_url: str) -> str:
    return _env.get_template("confirm.html.j2").render(
        t=TOKENS, username=username, confirm_url=confirm_url
    )


def send_confirmation(
    subscriber_id: int, username: str, email: str, settings: Settings
) -> None:
    """Issue the confirm token and email the confirmation link."""
    token = issue_token(subscriber_id, "confirm")
    confirm_url = f"{settings.public_base_url}/confirm?token={token}"
    mailer.send_email(
        render_confirmation(username, confirm_url), email, CONFIRM_SUBJECT, settings
    )
