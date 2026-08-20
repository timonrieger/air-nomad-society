from typing import Any

from pydantic import BaseModel


class Subscriber(BaseModel):
    """A subscriber's preferences as the digest job consumes them."""

    id: int
    username: str
    email: str
    token: str
    departure_city: str
    departure_iata: str
    currency: str
    min_nights: int
    max_nights: int
    min_days_ahead: int
    max_days_ahead: int
    favorites: list[str]
    excluded: list[str]

    @classmethod
    def from_row(cls, row: Any) -> "Subscriber":
        return cls(
            id=row.id,
            username=row.username,
            email=row.email,
            token=row.token,
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
