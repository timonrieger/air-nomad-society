from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.app.db import AirNomads


class Subscriber(BaseModel):
    """A subscriber's preferences as the digest job consumes them."""

    id: int = Field(description="Primary key in the air_nomads table")
    username: str = Field(description="Display name used in the email greeting")
    email: str = Field(description="Address the digest is sent to")
    departure_airports: list[str] = Field(
        description="IATA codes searches fly from; every one is searched"
    )
    currency: str = Field(description="ISO 4217 currency code for listed prices")
    min_nights: int = Field(description="Minimum nights per trip")
    max_nights: int = Field(description="Maximum nights per trip")
    min_days_ahead: int = Field(description="Search window start, days from today")
    max_days_ahead: int = Field(description="Search window end, days from today")
    favorites: list[str] = Field(
        description="Favorite country names, always searched for deals"
    )
    excluded: list[str] = Field(description="Country names never picked as random gems")
    confirmed: bool = Field(description="Whether the subscriber confirmed via email")

    @classmethod
    def from_row(cls, row: "AirNomads") -> "Subscriber":
        return cls(
            id=row.id,
            username=row.username,
            email=row.email,
            departure_airports=_split(row.departure_airports),
            currency=row.currency.upper(),
            min_nights=row.min_nights,
            max_nights=row.max_nights,
            min_days_ahead=row.min_days_ahead,
            max_days_ahead=row.max_days_ahead,
            favorites=_split(row.travel_countries),
            excluded=_split(row.excluded_countries),
            confirmed=row.confirmed_at is not None,
        )


def _split(joined: str | None) -> list[str]:
    return [part.strip() for part in joined.split(",")] if joined else []
