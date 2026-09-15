from datetime import date

from pydantic import BaseModel, Field


class WallDeal(BaseModel):
    """One anonymized deal card, display-ready. Prices are whole euros
    whatever currency the deal was emailed in, so cards stay comparable."""

    destination: str = Field(description="Destination city, country as fallback")
    departure_city: str = Field(description="Name of the departure city")
    price: int = Field(description="Round-trip price in euros")
    currency: str = Field(description='Display currency — always "EUR"')
    low_since: date = Field(
        description="The fare beat every price observed on its route since "
        "this date, as of the day it was found"
    )
    badge: str | None = Field(description="Streak-tier badge the deal earned")
    found_on: date = Field(description="Date the deal went out in a digest")
    link: str = Field(
        description="Booking deep link at the provider that found the fare"
    )
    image_url: str = Field(description="Destination image for the card")
