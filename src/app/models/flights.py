from datetime import date

from pydantic import BaseModel


class SearchQuery(BaseModel):
    """One round-trip search: origin -> destination inside a date window."""

    origin_iata: str
    destination_iata: str
    date_from: date  # earliest outbound departure
    date_to: date  # latest outbound departure
    min_nights: int
    max_nights: int
    currency: str


class FlightDeal(BaseModel):
    """The cheapest round trip a provider found for a query."""

    price: float
    currency: str
    departure_city: str
    departure_iata: str
    arrival_city: str
    arrival_iata: str
    arrival_country: str
    departs_on: date
    returns_on: date
    link: str
    via_city: str | None = None  # outbound stopover, if any
