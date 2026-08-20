"""Structural checks on `static/data.json`.

The digest job indexes this file by country name to pick destination images, and
builds the subscribe form's choices from it, so malformed entries surface as
runtime failures rather than validation errors.
"""

import json
from pathlib import Path

import pytest

DATA_PATH = Path(__file__).resolve().parent.parent / "src" / "data.json"


@pytest.fixture(scope="session")
def data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def test_top_level_keys(data: dict) -> None:
    assert set(data) == {"countries", "cities", "currencies", "images"}


def test_countries_are_named_with_unique_iso_codes(data: dict) -> None:
    countries = data["countries"]
    assert all(entry["country"].strip() for entry in countries)
    assert all(
        len(entry["code"]) == 2 and entry["code"].isalpha() and entry["code"].isupper()
        for entry in countries
    )
    assert len({entry["code"] for entry in countries}) == len(countries)


def test_cities_are_named_with_unique_iata_codes(data: dict) -> None:
    cities = data["cities"]
    assert all(entry["city"].strip() for entry in cities)
    assert all(
        len(entry["code"]) == 3 and entry["code"].isalpha() and entry["code"].isupper()
        for entry in cities
    )
    assert len({entry["code"] for entry in cities}) == len(cities)


def test_currencies_are_unique_iso_codes(data: dict) -> None:
    currencies = data["currencies"]
    assert all(
        len(code) == 3 and code.isalpha() and code.isupper() for code in currencies
    )
    assert len(set(currencies)) == len(currencies)


def test_every_image_entry_is_a_non_empty_list_of_urls(data: dict) -> None:
    """An empty list crashes the digest: `random.choice([])` raises IndexError.

    `notification_manager` only guards against a missing key, so a country
    present with no images is a live failure rather than a fallback.
    """
    for country, urls in data["images"].items():
        assert urls, f"{country} has no images; drop the key to use the fallback"
        assert all(url.startswith("https://") for url in urls), country
