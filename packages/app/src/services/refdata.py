"""Typed access to the reference data in `packages/app/src/data.json`."""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

DATA_PATH = Path(__file__).resolve().parent.parent / "data.json"

# The library URLs in data.json are full-resolution originals; every consumer
# (digest email, deal wall) renders them as ~600-800px cards, so one
# card-sized crop serves them all.
IMAGE_PARAMS = "w=800&auto=format&fit=crop&q=60"
FALLBACK_IMAGE = (
    f"https://images.unsplash.com/photo-1500835556837-99ac94a94552?{IMAGE_PARAMS}"
    "&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8VFJBVkVMfGVufDB8fDB8fHww"
)


class Country(BaseModel):
    country: str
    code: str
    region: str


class City(BaseModel):
    city: str
    code: str


class ReferenceData(BaseModel):
    countries: list[Country]
    cities: list[City]
    currencies: list[str]
    images: dict[str, list[str]]


@lru_cache
def load() -> ReferenceData:
    return ReferenceData.model_validate_json(DATA_PATH.read_text(encoding="utf-8"))


def country_choices() -> list[str]:
    return [country.country for country in load().countries]


def currency_choices() -> list[str]:
    return load().currencies


@lru_cache
def country_names() -> frozenset[str]:
    return frozenset(country_choices())


@lru_cache
def city_codes() -> frozenset[str]:
    return frozenset(city.code for city in load().cities)


def country_images(images: dict[str, list[str]], country: str) -> list[str]:
    """Card-sized images for a country; the shared fallback when it has none.

    Joined with a plain & — every library URL carries a query string, an
    invariant test_refdata guards."""
    urls = images.get(country)
    return [f"{url}&{IMAGE_PARAMS}" for url in urls] if urls else [FALLBACK_IMAGE]


@lru_cache
def regions() -> dict[str, list[str]]:
    """Country names per region, for the exclusion picker's region groups."""
    grouped: dict[str, list[str]] = {}
    for country in load().countries:
        grouped.setdefault(country.region, []).append(country.country)
    return dict(sorted(grouped.items()))
