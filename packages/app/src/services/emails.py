"""Renders the digest and confirmation emails and owns their subjects and links."""

import json
import random
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.config import Settings
from src.models.flights import RankedDeal
from src.services import mailer
from src.services.digest import DigestResult
from src.services.refdata import country_images
from src.services.selection import savings_badge, savings_percent
from src.services.tokens import issue_token

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

DIGEST_SUBJECT = "Fresh Flight Deals!"
CONFIRM_SUBJECT = "Confirm your subscription"

# The shared brand definition (one accent, one gray scale, one font stack);
# packages/web consumes the same file via the brand-theme plugin in vite.config.ts.
# Emails render on white with the light end of the scale, the web on the dark.
TOKENS: dict[str, str] = json.loads(
    (TEMPLATE_DIR.parent / "brand.json").read_text(encoding="utf-8")
)
# Rendered values are trusted internal data (usernames, provider results);
# autoescape stays off. Revisit when usernames become untrusted input.
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)  # noqa: S701 # nosec B701


def _anchor(price: float, baseline: float, currency: str) -> tuple[str, str | None]:
    """The "typically ~X" line and the earned tier badge, if any.

    Both come from the same rounded percent, so the badge never contradicts
    the savings the card shows."""
    savings = savings_percent(price, baseline)
    line = f"typically ~{baseline:.0f} {currency}"
    if savings is None:
        return line, None
    return f"{line} (−{savings}%)", savings_badge(savings)


def _present(
    ranked: RankedDeal,
    images: dict[str, list[str]],
    baseline: float | None,
    rng: random.Random,
) -> dict[str, Any]:
    deal = ranked.deal
    anchor, tier = (
        _anchor(deal.price, baseline, deal.currency) if baseline else (None, None)
    )
    badges = ["⭐ favorite" if ranked.source == "favorite" else "✨ discovery"]
    if tier:
        badges.append(tier)
    if ranked.first_time:
        badges.append("✨ new for you")
    return {
        "deal": deal,
        # One badge slot per card: provenance, then the earned savings tier;
        # the freshness badge (#17) appends here too.
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
    digest: DigestResult,
    images: dict[str, list[str]],
    base_url: str,
    favorites_configured: bool,
    rng: random.Random | None = None,
) -> str:
    # An empty digest is never sent (the cli skips it); rendering one is a bug.
    assert digest.deals
    picker = rng or random.Random()  # nosec B311 # picks photos, not secrets
    return _env.get_template("digest.html.j2").render(
        t=TOKENS,
        username=username,
        site_url=base_url,
        update_url=f"{base_url}/subscribe?token={update_token}",
        unsubscribe_url=f"{base_url}/unsubscribe?token={unsubscribe_token}",
        flights=[
            _present(ranked, images, digest.baseline_for(ranked), picker)
            for ranked in digest.deals
        ],
        # The add-favorites nudge renders only for subscribers who expect
        # favorite deals: with none configured, all-discoveries is the product.
        no_favorite_deals=favorites_configured
        and all(ranked.source != "favorite" for ranked in digest.deals),
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
