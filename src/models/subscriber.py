from typing import Any

from pydantic import BaseModel, Field


class Subscriber(BaseModel):
    """A subscriber's preferences as the digest job consumes them."""

    id: int = Field(description="Primary key in the air_nomads table")
    username: str = Field(description="Display name used in the email greeting")
    email: str = Field(description="Address the digest is sent to")
    departure_city: str = Field(description="Name of the departure city")
    departure_iata: str = Field(description="IATA code all searches fly from")
    currency: str = Field(description="ISO 4217 currency code for listed prices")
    min_nights: int = Field(description="Minimum nights per trip")
    max_nights: int = Field(description="Maximum nights per trip")
    min_days_ahead: int = Field(description="Search window start, days from today")
    max_days_ahead: int = Field(description="Search window end, days from today")
    favorites: list[str] = Field(
        description="Favorite country names, always searched for deals"
    )
    excluded: list[str] = Field(description="Country names never picked as random gems")

    @classmethod
    def from_row(cls, row: Any) -> "Subscriber":
        return cls(
            id=row.id,
            username=row.username,
            email=row.email,
            departure_city=row.departure_city,
            departure_iata=row.departure_iata,
            currency=row.currency.upper(),
            min_nights=row.min_nights,
            max_nights=row.max_nights,
            min_days_ahead=row.min_days_ahead,
            max_days_ahead=row.max_days_ahead,
            favorites=_split(row.travel_countries),
            excluded=_split(row.excluded_countries),
        )


def _split(joined: str | None) -> list[str]:
    return [part.strip() for part in joined.split(",")] if joined else []
