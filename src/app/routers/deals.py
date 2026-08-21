import time
from datetime import date

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from src.app.services.emails import savings_badge
from src.app.services.history import wall_deals
from src.app.services.refdata import city_names

router = APIRouter()

WALL_DEAL_COUNT = 12
# The wall only changes when a digest run writes sent_deal rows (weekly);
# the endpoint is public and CORS-open, so requests in between serve this
# process cache and the CDN header lets edges absorb repeat hits.
WALL_CACHE_SECONDS = 3600

_cache: tuple[float, list["WallDeal"]] | None = None


class WallDeal(BaseModel):
    """One anonymized deal on the public wall."""

    departure_city: str = Field(description="Name of the departure city")
    arrival_city: str | None = Field(description="Name of the destination city")
    arrival_country: str = Field(description="Name of the destination country")
    price: float = Field(description="Round-trip price in `currency`")
    currency: str = Field(description="ISO 4217 currency code of the price")
    savings_percent: int | None = Field(
        description="Whole-percent savings vs the route's typical price"
    )
    badge: str | None = Field(description="Savings-tier badge the deal earned")
    found_on: date = Field(description="Date the deal went out in a digest")


@router.get("/deals")
def read_deals(response: Response) -> list[WallDeal]:
    """Recent notable deals, aggregated across subscribers — no personal data."""
    global _cache
    # s-maxage: Vercel's edge only caches function responses that carry it.
    response.headers["Cache-Control"] = (
        f"public, max-age={WALL_CACHE_SECONDS}, s-maxage={WALL_CACHE_SECONDS}"
    )
    if _cache and time.monotonic() - _cache[0] < WALL_CACHE_SECONDS:
        return _cache[1]
    wall = [
        WallDeal(
            # Pre-0008 rows carry no name; reference data covers most codes.
            departure_city=row.departure_city
            or city_names().get(row.departure_iata, row.departure_iata),
            arrival_city=row.arrival_city,
            arrival_country=row.arrival_country,
            price=row.price,
            currency=row.currency,
            savings_percent=row.savings_percent,
            badge=(
                savings_badge(row.savings_percent)
                if row.savings_percent is not None
                else None
            ),
            found_on=row.sent_at.date(),
        )
        for row in wall_deals(WALL_DEAL_COUNT)
    ]
    _cache = (time.monotonic(), wall)
    return wall
