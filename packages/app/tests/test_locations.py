import pytest

from src.services import locations, refdata
from src.services.refdata import City, Country, ReferenceData


class FakeSource:
    def __init__(self, name: str, cities: list[City], countries: list[Country]) -> None:
        self.name = name
        self.cities = cities
        self.countries = countries

    def locations(self, city_limit: int) -> tuple[list[City], list[Country]]:
        return self.cities, self.countries


def city(name: str, code: str, provider: str) -> City:
    return City(city=name, code=code, providers=[provider])


TEQUILA = FakeSource(
    "tequila",
    [city("Munich", "MUC", "tequila"), city("Helsinki", "HEL", "tequila")],
    [
        Country(country="Finland", code="FI", region="Europe"),
        Country(country="Czechia", code="CZ", region="Europe"),
        Country(country="Aruba", code="AW", region="North America"),
    ],
)


@pytest.fixture
def saved(monkeypatch) -> list[ReferenceData]:
    before = ReferenceData(
        countries=[
            Country(country="Czech Republic", code="CZ", region="Europe"),
            Country(country="Finland", code="FI", region="Europe"),
            Country(country="Russia", code="RU", region="Europe"),
            # Added by an earlier sync, still without images.
            Country(country="Aruba", code="AW", region="North America"),
        ],
        cities=[city("Moscow", "MOW", "tequila")],
        currencies=["EUR"],
        images={"Czech Republic": ["cz"], "Finland": ["fi"], "Russia": ["ru"]},
    )
    writes: list[ReferenceData] = []
    monkeypatch.setattr(refdata, "load", lambda: before)
    monkeypatch.setattr(refdata, "save", writes.append)
    return writes


def test_sync_sorts_and_carries_images_by_country_code(saved) -> None:
    locations.sync_locations([TEQUILA])
    (after,) = saved
    assert [city.city for city in after.cities] == ["Helsinki", "Munich"]
    assert [c.country for c in after.countries] == ["Aruba", "Czechia", "Finland"]
    assert after.images == {"Czechia": ["cz"], "Finland": ["fi"]}
    assert after.currencies == ["EUR"]


def test_sync_unions_cities_across_providers(saved) -> None:
    other = FakeSource(
        "other",
        [city("München", "MUC", "other"), city("Memmingen", "FMM", "other")],
        [Country(country="Finland (other)", code="FI", region="Europe")],
    )
    locations.sync_locations([TEQUILA, other])
    (after,) = saved
    providers = {city.code: city.providers for city in after.cities}
    assert providers == {
        "FMM": ["other"],
        "HEL": ["tequila"],
        "MUC": ["tequila", "other"],
    }
    # The first source names shared cities and countries.
    assert "Munich" in [city.city for city in after.cities]
    assert "Finland" in [country.country for country in after.countries]
    # Sources keep their own lists untouched.
    assert TEQUILA.cities[0].providers == ["tequila"]
