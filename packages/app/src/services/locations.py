"""Refreshes the cities and countries in `data.json` from the providers."""

from src.services import refdata
from src.services.providers import LocationSource
from src.services.refdata import City, Country, ReferenceData

# Departure cities each provider contributes, by its own popularity ranking.
CITY_LIMIT = 1000


def sync_locations(sources: list[LocationSource]) -> None:
    """Rewrites cities and countries as the union over every source; a city
    lists each provider that searches from it, and the first source names
    a shared city or country. Images follow a renamed country by its code
    and are dropped with a removed one; new countries get none."""
    data = refdata.load()
    cities_by_code: dict[str, City] = {}
    countries_by_code: dict[str, Country] = {}
    for source in sources:
        source_cities, source_countries = source.locations(CITY_LIMIT)
        for city in source_cities:
            cities_by_code.setdefault(
                city.code, city.model_copy(update={"providers": []})
            ).providers += city.providers
        for country in source_countries:
            countries_by_code.setdefault(country.code, country)
    cities = list(cities_by_code.values())
    countries = list(countries_by_code.values())
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
                if previous.get(country.code) in data.images
            },
        )
    )
