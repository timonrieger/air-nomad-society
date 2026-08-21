from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.db import SentDeal, get_session
from src.app.services.refdata import country_images, load
from src.app.services.selection import savings_badge

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

WALL_DEAL_COUNT = 12
WALL_WINDOW_WEEKS = 4
# The wall only changes when a digest run writes sent_deal rows; the endpoint
# is public and CORS-open, and this header lets the CDN absorb repeat hits —
# one indexed query per edge miss is cheap enough.
WALL_CACHE_SECONDS = 3600


class WallDeal(BaseModel):
    """One anonymized deal card, display-ready: the prices are the integers
    the digest email printed, so the wall can never disagree with it."""

    destination: str = Field(description="Destination city, country as fallback")
    departure_city: str = Field(description="Name of the departure city")
    price: int = Field(description="Round-trip price in `currency` as emailed")
    currency: str = Field(description="ISO 4217 currency code of the prices")
    savings_percent: int | None = Field(
        description="Whole-percent savings vs the route's typical price"
    )
    usual_price: int | None = Field(
        description="The route's typical price as the email quoted it"
    )
    badge: str | None = Field(description="Savings-tier badge the deal earned")
    image_url: str = Field(description="Destination image for the card")


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
            image_url=country_images(images, row.arrival_country)[0],
        )
        for row in best[:WALL_DEAL_COUNT]
    ]
