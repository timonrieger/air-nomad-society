from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.app.services import refdata
from src.app.services.refdata import City

router = APIRouter()


class RefData(BaseModel):
    cities: list[City] = Field(description="Departure cities with IATA codes")
    currencies: list[str] = Field(description="ISO 4217 currency codes")
    countries: list[str] = Field(description="Destination country names")


@router.get("/refdata")
def reference_data() -> RefData:
    """The choice lists the subscription form is built from."""
    data = refdata.load()
    return RefData(
        cities=data.cities,
        currencies=data.currencies,
        countries=[country.country for country in data.countries],
    )
