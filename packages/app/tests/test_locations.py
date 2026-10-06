from src.services import locations, refdata
from src.services.refdata import City, Country, ReferenceData


class FakeSource:
    def locations(self, city_limit: int) -> tuple[list[City], list[Country]]:
        return (
            [City(city="Munich", code="MUC"), City(city="Helsinki", code="HEL")],
            [
                Country(country="Finland", code="FI", region="Europe"),
                Country(country="Czechia", code="CZ", region="Europe"),
                Country(country="Aruba", code="AW", region="North America"),
            ],
        )


def test_sync_sorts_and_carries_images_by_country_code(monkeypatch) -> None:
    before = ReferenceData(
        countries=[
            Country(country="Czech Republic", code="CZ", region="Europe"),
            Country(country="Finland", code="FI", region="Europe"),
            Country(country="Russia", code="RU", region="Europe"),
        ],
        cities=[City(city="Moscow", code="MOW")],
        currencies=["EUR"],
        images={"Czech Republic": ["cz"], "Finland": ["fi"], "Russia": ["ru"]},
    )
    saved: list[ReferenceData] = []
    monkeypatch.setattr(refdata, "load", lambda: before)
    monkeypatch.setattr(refdata, "save", saved.append)
    locations.sync_locations(FakeSource())
    (after,) = saved
    assert [city.city for city in after.cities] == ["Helsinki", "Munich"]
    assert [c.country for c in after.countries] == ["Aruba", "Czechia", "Finland"]
    assert after.images == {"Czechia": ["cz"], "Finland": ["fi"]}
    assert after.currencies == ["EUR"]
