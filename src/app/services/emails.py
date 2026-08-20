"""Renders the digest and confirmation emails and owns their subjects and links."""

import json
import random
from datetime import date
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.app.config import Settings
from src.app.models.flights import FlightDeal, RankedDeal
from src.app.services import mailer
from src.app.services.digest import DigestResult
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

# Rendered values are trusted internal data (usernames, provider results);
# autoescape stays off. Revisit when usernames become untrusted input.
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)  # noqa: S701 # nosec B701


def _facts(deal: FlightDeal) -> str:
    """The quality line on a deal card, e.g. "direct · 2h35 · dep 10:40"."""
    if deal.stopovers:
        label = "stop" if deal.stopovers == 1 else "stops"
        via = dict.fromkeys(deal.via_cities + deal.return_via_cities)
        stops = f"{deal.stopovers} {label} via {', '.join(via)}"
    else:
        stops = "direct"
    hours, minutes = divmod(deal.duration_minutes, 60)
    return f"{stops} · {hours}h{minutes:02d} · dep {deal.departs_at:%H:%M}"


def _window(start: date, end: date) -> str:
    """The searched departure window, e.g. "Sep 1–30" or "Sep 26 – Oct 12"."""
    if (start.year, start.month) == (end.year, end.month):
        return f"{start:%b} {start.day}–{end.day}"
    if start.year == end.year:
        return f"{start:%b} {start.day} – {end:%b} {end.day}"
    return f"{start:%b} {start.day}, {start.year} – {end:%b} {end.day}, {end.year}"


def _present(
    ranked: RankedDeal, window: str, images: dict[str, list[str]], rng: random.Random
) -> dict[str, Any]:
    deal = ranked.deal
    country_images = images.get(deal.arrival_country)
    return {
        "deal": deal,
        # One badge slot per card: provenance now, savings tier / freshness later.
        "badges": ["⭐ favorite" if ranked.source == "favorite" else "✨ discovery"],
        # "depart", not "travel between": the window bounds outbound departures,
        # so the example trip's return may legitimately fall after it.
        "dates": f"depart {window} · e.g. {deal.departs_at:%d.%m}–{deal.returns_at:%d.%m}",
        "facts": _facts(deal),
        "image_url": rng.choice(country_images) if country_images else FALLBACK_IMAGE,
    }


def render_digest(
    username: str,
    update_token: str,
    unsubscribe_token: str,
    digest: DigestResult,
    images: dict[str, list[str]],
    base_url: str,
    rng: random.Random | None = None,
) -> str:
    # An empty digest is never sent (the cli skips it); rendering one is a bug.
    assert digest.deals
    picker = rng or random.Random()  # nosec B311 # picks photos, not secrets
    window = _window(digest.window_start, digest.window_end)
    return _env.get_template("digest.html.j2").render(
        t=TOKENS,
        username=username,
        site_url=base_url,
        update_url=f"{base_url}/subscribe?token={update_token}",
        unsubscribe_url=f"{base_url}/unsubscribe?token={unsubscribe_token}",
        flights=[_present(ranked, window, images, picker) for ranked in digest.deals],
        no_favorite_deals=all(ranked.source != "favorite" for ranked in digest.deals),
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
