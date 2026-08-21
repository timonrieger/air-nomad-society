"""One personalized reason per picked deal, from an AI model.

Provider-abstract: any OpenAI-compatible chat-completions endpoint works
(base URL, model, and key come from settings). Optional by design — no API
key means no reasons, and any failure means no reasons. The digest never
crashes on this path."""

import json
import logging

import requests

from src.app.config import Settings
from src.app.models.flights import RankedDeal
from src.app.models.subscriber import Subscriber
from src.app.services.digest import DigestResult
from src.app.services.emails import deal_facts

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 120
MAX_OUTPUT_TOKENS = 1000

SYSTEM_PROMPT = """\
You write one short reason per flight deal for a personalized weekly deal
digest. Each reason tells this subscriber why their deal was picked: what it
beat (runner-ups on the same route search), how it compares to the route's
typical price, comfort (direct, duration, departure time), or that it's one
of their favorite countries or a fresh discovery. Be concrete and specific,
warm but not salesy, at most 120 characters per reason. Never invent facts
not present in the data.

Reply with ONLY a JSON object mapping each deal's "id" to its reason string."""


def _card(ranked: RankedDeal) -> dict[str, object]:
    deal = ranked.deal
    return {
        "route": f"{deal.departure_city}–{deal.arrival_city}, {deal.arrival_country}",
        "price": f"{deal.price:.0f} {deal.currency}",
        "facts": deal_facts(deal),
        "dates": f"{deal.departs_at:%d.%m}–{deal.returns_at:%d.%m}",
    }


def _payload(
    subscriber: Subscriber, digest: DigestResult, baselines: dict[str, float]
) -> dict[str, object]:
    return {
        "subscriber": {
            "favorite_countries": subscriber.favorites,
            "trip_length_nights": [subscriber.min_nights, subscriber.max_nights],
        },
        "deals": [
            {
                "id": ranked.deal.arrival_iata,
                "picked_as": ranked.source,
                **_card(ranked),
                "typical_price": baselines.get(ranked.deal.arrival_iata),
                "beat_these_runner_ups": [
                    _card(runner_up)
                    for runner_up in digest.runner_ups.get(ranked.deal.arrival_iata, [])
                ],
            }
            for ranked in digest.deals
        ],
    }


def deal_reasons(
    subscriber: Subscriber,
    digest: DigestResult,
    baselines: dict[str, float],
    settings: Settings,
) -> dict[str, str]:
    """Reason per deal, keyed by arrival_iata; empty when unconfigured or failed."""
    if not settings.ai_api_key:
        return {}
    try:
        response = requests.post(
            f"{settings.ai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.ai_api_key}"},
            json={
                "model": settings.ai_model,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(
                            _payload(subscriber, digest, baselines)
                        ),
                    },
                ],
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        content = content.strip().removeprefix("```json").removesuffix("```")
        reasons = json.loads(content)
        return {
            arrival_iata: reason
            for arrival_iata, reason in reasons.items()
            if isinstance(reason, str)
        }
    except Exception:
        # The reasoning line is a garnish: any failure just means no line.
        logger.warning("deal reasons failed for %s", subscriber.email, exc_info=True)
        return {}
