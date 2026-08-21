import argparse
import logging
import sys
from datetime import timedelta

from src.app.services import emails, mailer, refdata
from src.app.config import get_settings
from src.app.db import load_subscribers, purge_unconfirmed
from src.app.models.subscriber import Cadence
from src.app.services.digest import build_digest
from src.app.services.history import (
    RecordingProvider,
    last_sent_at,
    record_sent_deals,
    route_baselines,
    sent_history,
)
from src.app.services.reasons import deal_reasons
from src.app.services.providers import FlightProvider
from src.app.services.providers.tequila import TequilaProvider
from src.app.services.tokens import issue_token

logger = logging.getLogger(__name__)

# Minimum days since the last delivered digest before the weekly run sends
# again, per cadence — each between its nominal interval's neighboring runs
# (biweekly: 7 and 14 days, monthly: 21 and 28), so subscribers skip exactly
# the right number of runs with no dispatch rework.
CADENCE_GAP_DAYS: dict[Cadence, int] = {"weekly": 0, "biweekly": 10, "monthly": 24}


def run_digest(provider: FlightProvider) -> int:
    """Sends the digest to every subscriber; one failure never blocks the rest.

    Returns the number of failed subscribers (also the exit code, so a
    partial failure still turns the scheduled run red).
    """
    settings = get_settings()
    data = refdata.load()
    purged = purge_unconfirmed()
    if purged:
        logger.info("purged %d subscribers that never confirmed", purged)
    subscribers = load_subscribers(settings.digest_only_id)
    logger.info("sending digest to %d subscribers", len(subscribers))
    recording = RecordingProvider(provider)
    failures = 0
    for subscriber in subscribers:
        try:
            gap = CADENCE_GAP_DAYS[subscriber.cadence]
            last = last_sent_at(subscriber.id) if gap else None
            if last and last > recording.started_at - timedelta(days=gap):
                logger.info("not due yet for %s, skipping", subscriber.email)
                continue
            result = build_digest(
                subscriber,
                recording,
                data.countries,
                history=sent_history(subscriber.id),
                # before=started_at: the run's own candidates never anchor
                # themselves.
                baselines_for=lambda routes: route_baselines(
                    routes, subscriber.currency, before=recording.started_at
                ),
            )
            if not result.deals:
                logger.info("no deals for %s, skipping digest", subscriber.email)
                continue
            deal_reasons(subscriber, result, settings)
            html = emails.render_digest(
                username=subscriber.username,
                update_token=issue_token(subscriber.id, "update"),
                unsubscribe_token=issue_token(subscriber.id, "unsubscribe"),
                digest=result,
                images=data.images,
                base_url=settings.public_base_url,
                favorites_configured=bool(subscriber.favorites),
            )
            mailer.send_email(html, subscriber.email, emails.DIGEST_SUBJECT, settings)
            record_sent_deals(subscriber.id, result)
            logger.info("sent digest to %s", subscriber.email)
        except Exception:
            failures += 1
            logger.exception("digest failed for %s", subscriber.email)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ans")
    parser.add_argument(
        "command", choices=["digest"], help="search deals and email every subscriber"
    )
    parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    provider = TequilaProvider(settings.tequila_endpoint, settings.tequila_api_key)
    return run_digest(provider)


if __name__ == "__main__":
    sys.exit(main())
