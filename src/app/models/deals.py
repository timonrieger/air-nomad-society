from datetime import date

from pydantic import BaseModel, Field


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
    found_on: date = Field(description="Date the deal went out in a digest")
    image_url: str = Field(description="Destination image for the card")
