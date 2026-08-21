"""Loading and structural checks for `src/app/data.json`.

The digest job indexes this file by country name to pick destination images,
and builds the subscribe form's choices from it, so malformed entries surface
as runtime failures rather than validation errors.
"""

from src.app.services import refdata


def test_loads_and_validates() -> None:
    data = refdata.load()
    assert len(data.countries) > 150
    assert len(data.cities) > 400
    assert data.images


def test_lookup_helpers_cover_the_data() -> None:
    data = refdata.load()
    assert len(refdata.country_choices()) == len(data.countries)
    assert refdata.city_codes() == {city.code for city in data.cities}


def test_countries_are_named_with_unique_iso_codes() -> None:
    countries = refdata.load().countries
    assert all(entry.country.strip() for entry in countries)
    assert all(
        len(entry.code) == 2 and entry.code.isalpha() and entry.code.isupper()
        for entry in countries
    )
    assert len({entry.code for entry in countries}) == len(countries)


def test_cities_are_named_with_unique_iata_codes() -> None:
    cities = refdata.load().cities
    assert all(entry.city.strip() for entry in cities)
    assert all(
        len(entry.code) == 3 and entry.code.isalpha() and entry.code.isupper()
        for entry in cities
    )
    assert len({entry.code for entry in cities}) == len(cities)


def test_currencies_are_unique_iso_codes() -> None:
    currencies = refdata.load().currencies
    assert all(
        len(code) == 3 and code.isalpha() and code.isupper() for code in currencies
    )
    assert len(set(currencies)) == len(currencies)


def test_every_country_has_images_and_no_key_is_orphaned() -> None:
    """Coverage both ways: a country without images renders the generic
    fallback on real cards, and a key without a country is dead weight."""
    data = refdata.load()
    countries = {entry.country for entry in data.countries}
    assert countries - set(data.images) == set()
    assert set(data.images) - countries == set()


def test_every_image_entry_is_a_non_empty_list_of_urls() -> None:
    """An empty list crashes the digest: `random.choice([])` raises IndexError."""
    for country, urls in refdata.load().images.items():
        assert urls, f"{country} has no images; drop the key to use the fallback"
        assert all(url.startswith("https://") for url in urls), country
