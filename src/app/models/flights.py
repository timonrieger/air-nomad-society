from datetime import datetime, date

from pydantic import BaseModel, Field


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
    stopovers: int = Field(description="Stopover count on the outbound leg")
    link: str = Field(description="Deep link to book this itinerary")
    via_city: str | None = Field(
        default=None, description="Stopover city on the outbound leg, if any"
    )
