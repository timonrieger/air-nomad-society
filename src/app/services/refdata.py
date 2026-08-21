"""Typed access to the reference data in `src/app/data.json`."""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

DATA_PATH = Path(__file__).resolve().parent.parent / "data.json"


class Country(BaseModel):
    country: str
    code: str


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


@lru_cache
def city_names() -> dict[str, str]:
    return {city.code: city.city for city in load().cities}
