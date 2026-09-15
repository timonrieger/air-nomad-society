from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import SentDeal, get_session
from src.models.deals import WallDeal
from src.models.flights import LowClaim
from src.services.history import route_observations
from src.services.refdata import country_images, load
from src.services.selection import low_badge, price_low_since

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

WALL_DEAL_COUNT = 12
WALL_WINDOW_WEEKS = 4
WALL_CACHE_SECONDS = 3600


def _eur_quality(row: SentDeal) -> float:
    """The stored native quality score, normalized to euros."""
    return row.quality_score * row.price_eur / row.price


@router.get("/deals")
def read_deals(session: SessionDep, response: Response) -> list[WallDeal]:
    """Recent notable deals, aggregated across subscribers — no personal data."""
    # s-maxage: Vercel's edge only caches function responses that carry it.
    response.headers["Cache-Control"] = (
        f"public, max-age={WALL_CACHE_SECONDS}, s-maxage={WALL_CACHE_SECONDS}"
    )
    now = datetime.now()
    since = now - timedelta(weeks=WALL_WINDOW_WEEKS)
    rows = session.scalars(
        select(SentDeal)
        .where(SentDeal.sent_at >= since)
        .order_by(SentDeal.sent_at.desc())
    )
    # One card per destination — breadth sells better than three fares to
    # the same city. The best EUR quality wins; ties keep the latest send.
    unique: dict[str, SentDeal] = {}
    for row in rows:
        city = row.arrival_city or row.arrival_country
        if city not in unique or _eur_quality(row) < _eur_quality(unique[city]):
            unique[city] = row
    # Never store claims: each card replays against observations before its
    # own sent_at, reproducing the send-time claim under the current algorithm.
    observations = route_observations(
        {row.route for row in unique.values()}, before=now
    )
    # The cheapest, most comfortable dozen with a claim make the wall;
    # within it the longest-standing lows lead.
    best: list[tuple[SentDeal, LowClaim]] = []
    for row in sorted(unique.values(), key=_eur_quality):
        claim = price_low_since(
            observations.get(row.route, []), row.price_eur, before=row.sent_at
        )
        if claim is not None:
            best.append((row, claim))
            if len(best) == WALL_DEAL_COUNT:
                break
    best.sort(key=lambda pair: -pair[1].weeks)
    images = load().images
    return [
        WallDeal(
            destination=row.arrival_city or row.arrival_country,
            departure_city=row.departure_city or row.departure_iata,
            price=int(row.price_eur),  # int(): whole units, like the email
            currency="EUR",
            low_since=claim.since.date(),
            badge=low_badge(claim.weeks),
            found_on=row.sent_at.date(),
            link=row.link,
            image_url=country_images(images, row.arrival_country)[0],
        )
        for row, claim in best
    ]
