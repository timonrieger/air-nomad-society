from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.app.services.history import wall_deals

router = APIRouter()

WALL_DEAL_COUNT = 12


class WallDeal(BaseModel):
    """One anonymized deal on the public wall."""

    departure_city: str | None = Field(description="Name of the departure city")
    arrival_city: str | None = Field(description="Name of the destination city")
    arrival_country: str = Field(description="Name of the destination country")
    price: float = Field(description="Round-trip price in `currency`")
    currency: str = Field(description="ISO 4217 currency code of the price")
    savings_percent: int | None = Field(
        description="Whole-percent savings vs the route's typical price"
    )
    found_on: date = Field(description="Date the deal went out in a digest")


@router.get("/deals")
def read_deals() -> list[WallDeal]:
    """Recent notable deals, aggregated across subscribers — no personal data."""
    return [
        WallDeal(
            departure_city=row.departure_city,
            arrival_city=row.arrival_city,
            arrival_country=row.arrival_country,
            price=row.price,
            currency=row.currency,
            savings_percent=savings,
            found_on=row.sent_at.date(),
        )
        for row, savings in wall_deals(WALL_DEAL_COUNT)
    ]
