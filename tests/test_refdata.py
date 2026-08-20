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
    assert refdata.city_name(data.cities[0].code) == data.cities[0].city
