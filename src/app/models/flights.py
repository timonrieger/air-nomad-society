from datetime import datetime, date
from typing import Literal

from pydantic import BaseModel, Field

DealSource = Literal["favorite", "discovery"]


class SearchQuery(BaseModel):
    """One round-trip search: origin -> destination inside a date window."""

    origin_iata: str = Field(description="IATA code of the departure city")
    destination_iata: str = Field(description="IATA code of the destination")
    date_from: date = Field(description="Earliest allowed outbound departure date")
    date_to: date = Field(description="Latest allowed outbound departure date")
    min_nights: int = Field(description="Minimum nights at the destination")
    max_nights: int = Field(description="Maximum nights at the destination")
    currency: str = Field(description="ISO 4217 currency code for prices")


class FlightDeal(BaseModel):
    """One round-trip itinerary a provider found for a query."""

    price: float = Field(description="Total round-trip price in `currency`")
    currency: str = Field(description="ISO 4217 currency code of the price")
    departure_city: str = Field(description="Name of the departure city")
    departure_iata: str = Field(description="IATA code of the departure city")
    arrival_city: str = Field(description="Name of the destination city")
    arrival_iata: str = Field(description="IATA code of the destination city")
    arrival_country: str = Field(description="Name of the destination country")
    departs_at: datetime = Field(description="Outbound departure, local time")
    returns_at: datetime = Field(description="Return arrival, local time")
    duration_minutes: int = Field(description="Outbound leg duration in minutes")
    via_cities: list[str] = Field(
        default_factory=list,
        description="Stopover cities on the outbound leg; empty means direct",
    )
    return_via_cities: list[str] = Field(
        default_factory=list,
        description="Stopover cities on the return leg; empty means direct",
    )
    link: str = Field(description="Deep link to book this itinerary")

    @property
    def stopovers(self) -> int:
        """Total stopovers across both legs; 0 means direct both ways."""
        return len(self.via_cities) + len(self.return_via_cities)

    @property
    def facts(self) -> str:
        """The quality line, e.g. "direct · 2h35 · dep 10:40"."""
        stops = "with stopover" if self.stopovers else "direct"
        hours, minutes = divmod(self.duration_minutes, 60)
        return f"{stops} · {hours}h{minutes:02d} · dep {self.departs_at:%H:%M}"

    @property
    def trip_dates(self) -> str:
        """The found trip's dates, e.g. "03.09–08.09"."""
        return f"{self.departs_at:%d.%m}–{self.returns_at:%d.%m}"


class RankedDeal(BaseModel):
    """A digest pick: the deal, where it came from, and how good it is."""

    deal: FlightDeal
    source: DealSource = Field(description="Favorite-country pick or random discovery")
    score: float = Field(
        description="Ranking score: quality inflated by freshness penalties; "
        "lower is better"
    )
    runner_ups: list["RankedDeal"] = Field(
        default_factory=list,
        description="Beaten candidates from the same search, best score first",
    )
    reason: str | None = Field(
        default=None, description="AI reasoning line shown on the deal card"
    )
    first_time: bool = Field(
        default=False,
        description="Destination country never emailed to this subscriber before",
    )
    origin_iata: str = Field(
        description="The searched departure airport this pick came from — the "
        "partition key for price observations",
    )
