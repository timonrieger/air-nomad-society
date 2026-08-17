"""Typed access to the reference data in `static/data.json`."""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

DATA_PATH = Path(__file__).resolve().parent.parent / "static" / "data.json"


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


def departure_choices() -> list[str]:
    return [f"{city.city} | {city.code}" for city in load().cities]


def country_choices() -> list[str]:
    return [country.country for country in load().countries]


def currency_choices() -> list[str]:
    return load().currencies
