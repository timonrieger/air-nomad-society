from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from src.services import refdata

if TYPE_CHECKING:
    from src.db import AirNomads

Cadence = Literal["weekly", "biweekly", "monthly"]


def _all_known(values: list[str], known: frozenset[str], label: str) -> list[str]:
    # Rejecting duplicates also bounds every list at its reference data.
    if len(set(values)) != len(values):
        raise ValueError(f"duplicate {label}")
    unknown = set(values) - known
    if unknown:
        raise ValueError(f"unknown {label}: {', '.join(sorted(unknown))}")
    return values


class SubscriptionIn(BaseModel):
    """The subscribe/update request body, validated against reference data."""

    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    departure_airports: list[str] = Field(min_length=1, max_length=5)
    currency: str
    min_nights: int = Field(ge=1)
    max_nights: int = Field(ge=1)
    min_days_ahead: int = Field(ge=1, le=365)
    max_days_ahead: int = Field(ge=1, le=365)
    # Required on the wire: a defaulted field would let a stale client
    # silently reset a saved preference on update.
    cadence: Cadence
    gem_count: int = Field(ge=0, le=10)
    # Capped like gem_count: every favorite is searched in every digest, so
    # an unbounded list is an unbounded Tequila bill. Empty is fine — that
    # subscriber's digest is pure discoveries.
    favorite_countries: list[str] = Field(max_length=10)
    excluded_countries: list[str] = []

    @field_validator("departure_airports")
    @classmethod
    def _known_cities(cls, value: list[str]) -> list[str]:
        return _all_known(value, refdata.city_codes(), "departure city codes")

    @field_validator("currency")
    @classmethod
    def _known_currency(cls, value: str) -> str:
        if value not in refdata.currency_choices():
            raise ValueError("unknown currency")
        return value

    @field_validator("favorite_countries", "excluded_countries")
    @classmethod
    def _known_countries(cls, value: list[str]) -> list[str]:
        return _all_known(value, refdata.country_names(), "countries")

    @model_validator(mode="after")
    def _ranges(self) -> "SubscriptionIn":
        if self.max_nights <= self.min_nights:
            raise ValueError("max_nights must be greater than min_nights")
        if self.max_days_ahead <= self.min_days_ahead:
            raise ValueError("max_days_ahead must be greater than min_days_ahead")
        search_range = self.max_days_ahead - self.min_days_ahead
        if self.max_nights > search_range:
            raise ValueError(
                f"max_nights ({self.max_nights}) cannot exceed the search "
                f"range duration ({search_range} days)"
            )
        return self


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
    cadence: Cadence = Field(description="How often the digest is sent")
    gem_count: int = Field(description="Surprise discoveries per digest")
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
            cadence=row.cadence,
            gem_count=row.gem_count,
            favorites=_split(row.travel_countries),
            excluded=_split(row.excluded_countries),
            confirmed=row.confirmed_at is not None,
        )


def _split(joined: str | None) -> list[str]:
    return [part.strip() for part in joined.split(",")] if joined else []
