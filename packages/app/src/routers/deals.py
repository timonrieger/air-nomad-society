from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import SentDeal, get_session
from src.models.deals import WallDeal
from src.services.refdata import country_images, load
from src.services.selection import savings_badge

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

WALL_DEAL_COUNT = 12
WALL_WINDOW_WEEKS = 4
WALL_CACHE_SECONDS = 3600


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
        .where(SentDeal.sent_at >= since)
        .order_by(SentDeal.sent_at.desc())
    )
    unique: dict[tuple[str, str, float, str], SentDeal] = {}
    for row in rows:  # newest first: the latest send of a route+price wins
        unique.setdefault(
            (row.departure_iata, row.arrival_iata, row.price, row.currency), row
        )
    best = sorted(unique.values(), key=lambda row: -(row.savings_percent or 0))
    images = load().images
    return [
        WallDeal(
            destination=row.arrival_city or row.arrival_country,
            departure_city=row.departure_city or row.departure_iata,
            price=int(row.price),  # int(): the email prints prices this way
            currency=row.currency,
            savings_percent=row.savings_percent,
            usual_price=row.usual_price,
            badge=(
                savings_badge(row.savings_percent)
                if row.savings_percent is not None
                else None
            ),
            found_on=row.sent_at.date(),
            link=row.link,
            image_url=country_images(images, row.arrival_country)[0],
        )
        for row in best[:WALL_DEAL_COUNT]
    ]
