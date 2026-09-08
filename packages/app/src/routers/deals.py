from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import SentDeal, get_session
from src.models.deals import WallDeal
from src.services.refdata import country_images, load
from src.services.selection import SAVINGS_TIERS, savings_badge

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

WALL_DEAL_COUNT = 12
WALL_WINDOW_WEEKS = 4
WALL_CACHE_SECONDS = 3600
# Every wall card must earn at least the lowest savings badge: the wall
# sells subscriptions, and a card without a proven discount sells nothing.
WALL_MIN_SAVINGS = SAVINGS_TIERS[-1][0]


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
    since = datetime.now() - timedelta(weeks=WALL_WINDOW_WEEKS)
    rows = session.scalars(
        select(SentDeal)
        .where(SentDeal.sent_at >= since, SentDeal.savings_percent >= WALL_MIN_SAVINGS)
        .order_by(SentDeal.sent_at.desc())
    )
    # One card per destination — breadth sells better than three fares to
    # the same city. The best EUR quality wins; ties keep the latest send.
    unique: dict[str, SentDeal] = {}
    for row in rows:
        city = row.arrival_city or row.arrival_country
        if city not in unique or _eur_quality(row) < _eur_quality(unique[city]):
            unique[city] = row
    # The cheapest, most comfortable dozen make the wall; within it the
    # deepest discounts lead.
    best = sorted(unique.values(), key=_eur_quality)
    best = sorted(best[:WALL_DEAL_COUNT], key=lambda row: -(row.savings_percent or 0))
    images = load().images
    wall: list[WallDeal] = []
    for row in best:
        # The savings filter guarantees an anchored row.
        assert row.savings_percent is not None and row.usual_price is not None
        wall.append(
            WallDeal(
                destination=row.arrival_city or row.arrival_country,
                departure_city=row.departure_city or row.departure_iata,
                price=int(row.price_eur),  # int(): whole units, like the email
                currency="EUR",
                savings_percent=row.savings_percent,
                usual_price=round(row.usual_price * row.price_eur / row.price),
                badge=savings_badge(row.savings_percent),
                found_on=row.sent_at.date(),
                link=row.link,
                image_url=country_images(images, row.arrival_country)[0],
            )
        )
    return wall
