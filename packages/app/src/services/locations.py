"""Refreshes the cities and countries in `data.json` from the providers."""

from src.services import refdata
from src.services.providers import LocationSource
from src.services.refdata import ReferenceData

# Departure cities offered in the subscribe form, by provider popularity.
CITY_LIMIT = 1000


def sync_locations(source: LocationSource) -> None:
    """Rewrites cities and countries; images follow a renamed country by its
    code and are dropped with a removed one."""
    data = refdata.load()
    cities, countries = source.locations(CITY_LIMIT)
    countries.sort(key=lambda country: country.country.casefold())
    cities.sort(key=lambda city: city.city.casefold())
    previous = {country.code: country.country for country in data.countries}
    refdata.save(
        ReferenceData(
            countries=countries,
            cities=cities,
            currencies=data.currencies,
            images={
                country.country: data.images[previous[country.code]]
                for country in countries
                if country.code in previous
            },
        )
    )
