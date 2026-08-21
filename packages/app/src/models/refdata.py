from pydantic import BaseModel, Field

from src.services.refdata import City


class RefData(BaseModel):
    """The /refdata response: the choice lists the subscription form is built from."""

    cities: list[City] = Field(description="Departure cities with IATA codes")
    currencies: list[str] = Field(description="ISO 4217 currency codes")
    countries: list[str] = Field(description="Destination country names")
    regions: dict[str, list[str]] = Field(description="Country names per region")
