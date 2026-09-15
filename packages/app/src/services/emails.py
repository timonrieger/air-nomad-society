"""Renders the digest and confirmation emails and owns their subjects and links."""

import json
import random
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.config import Settings
from src.models.flights import RankedDeal
from src.services import mailer
from src.services.refdata import country_images
from src.services.selection import low_badge
from src.services.tokens import issue_token

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

DIGEST_SUBJECT = "Fresh Flight Deals!"
CONFIRM_SUBJECT = "Confirm your subscription"

# The shared brand definition
TOKENS: dict[str, str] = json.loads(
    (TEMPLATE_DIR.parent / "brand.json").read_text(encoding="utf-8")
)
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)


def _present(
    ranked: RankedDeal,
    images: dict[str, list[str]],
    rng: random.Random,
) -> dict[str, Any]:
    deal = ranked.deal
    tier = low_badge(ranked.low.weeks) if ranked.low else None
    anchor = (
        f"lowest price since {ranked.low.since:%b %d}" if ranked.low and tier else None
    )
    badges = ["⭐ favorite" if ranked.source == "favorite" else "✨ discovery"]
    if tier:
        badges.append(tier)
    if ranked.first_time:
        badges.append("✨ new for you")
    return {
        "deal": deal,
        "badges": badges,
        "anchor": anchor,
        "reason": ranked.reason,
        "dates": deal.trip_dates,
        "facts": deal.facts,
        "image_url": rng.choice(country_images(images, deal.arrival_country)),
    }


def render_digest(
    username: str,
    update_token: str,
    unsubscribe_token: str,
    deals: list[RankedDeal],
    images: dict[str, list[str]],
    base_url: str,
    rng: random.Random | None = None,
) -> str:
    # An empty digest is never sent
    assert deals
    picker = rng or random.Random()  # nosec B311 # picks photos, not secrets
    return _env.get_template("digest.html.j2").render(
        t=TOKENS,
        username=username,
        site_url=base_url,
        update_url=f"{base_url}/subscribe?token={update_token}",
        unsubscribe_url=f"{base_url}/unsubscribe?token={unsubscribe_token}",
        flights=[_present(ranked, images, picker) for ranked in deals],
    )


def render_announcement(
    username: str,
    paragraphs: list[str],
    update_token: str,
    unsubscribe_token: str,
    base_url: str,
) -> str:
    """A product-update email: the supplied paragraphs in the brand frame."""
    return _env.get_template("announcement.html.j2").render(
        t=TOKENS,
        username=username,
        paragraphs=paragraphs,
        site_url=base_url,
        update_url=f"{base_url}/subscribe?token={update_token}",
        unsubscribe_url=f"{base_url}/unsubscribe?token={unsubscribe_token}",
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
