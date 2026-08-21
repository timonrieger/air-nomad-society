"""One personalized reason per picked deal, from an AI model.

Provider-abstract: any OpenAI-compatible chat-completions endpoint works
(base URL, model, and key come from settings). Optional by design — no API
key means no reasons, and any failure means no reasons. The digest never
crashes on this path."""

import json
import logging

import requests

from src.app.config import Settings
from src.app.models.flights import FlightDeal, RankedDeal
from src.app.models.subscriber import Subscriber

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 120
# Per-deal output allowance plus headroom, so a favorites-heavy digest's
# reasons JSON never gets cut off mid-object.
TOKENS_PER_REASON = 60
TOKEN_HEADROOM = 200
# The prompt asks for ≤120 chars; reasons wildly past that are dropped, not
# rendered as a paragraph on the card.
REASON_MAX_CHARS = 200

SYSTEM_PROMPT = """\
You write one short reason per flight deal for a personalized weekly deal
digest. Each reason tells this subscriber why their deal was picked: what it
beat (runner-ups on the same route search), how it compares to the route's
typical price, comfort (direct, duration, departure time), or that it's one
of their favorite countries or a fresh discovery. Be concrete and specific,
warm but not salesy, at most 120 characters per reason. Never invent facts
not present in the data.

Reply with ONLY a JSON object mapping each deal's "id" to its reason string."""


def _card(deal: FlightDeal) -> dict[str, object]:
    return {
        "route": f"{deal.departure_city}–{deal.arrival_city}, {deal.arrival_country}",
        "price": f"{deal.price:.0f} {deal.currency}",
        "facts": deal.facts,
        "dates": deal.trip_dates,
    }


def _payload(
    subscriber: Subscriber,
    deals: list[RankedDeal],
    baselines: dict[tuple[str, str], float],
) -> dict[str, object]:
    return {
        "subscriber": {
            "favorite_countries": subscriber.favorites,
            "trip_length_nights": [subscriber.min_nights, subscriber.max_nights],
        },
        "deals": [
            {
                "id": index,
                "picked_as": ranked.source,
                **_card(ranked.deal),
                "typical_price": baselines.get(
                    (ranked.origin_iata, ranked.deal.arrival_iata)
                ),
                "beat_these_runner_ups": [
                    _card(runner_up.deal) for runner_up in ranked.runner_ups
                ],
            }
            for index, ranked in enumerate(deals)
        ],
    }


def deal_reasons(
    subscriber: Subscriber,
    deals: list[RankedDeal],
    baselines: dict[tuple[str, str], float],
    settings: Settings,
) -> None:
    """Attach one reason per pick in place; a no-op when unconfigured or failed."""
    if not settings.ai_api_key:
        return
    try:
        response = requests.post(
            f"{settings.ai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.ai_api_key}"},
            json={
                "model": settings.ai_model,
                "max_tokens": TOKEN_HEADROOM + TOKENS_PER_REASON * len(deals),
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(
                            _payload(subscriber, deals, baselines),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    },
                ],
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        content = content.removeprefix("```json").removeprefix("```")
        content = content.removesuffix("```")
        reasons = json.loads(content)
        for index, ranked in enumerate(deals):
            reason = reasons.get(str(index))
            if isinstance(reason, str) and 0 < len(reason) <= REASON_MAX_CHARS:
                ranked.reason = reason
    except Exception:
        # The reasoning line is a garnish: any failure just means no line.
        logger.warning("deal reasons failed for %s", subscriber.email, exc_info=True)
