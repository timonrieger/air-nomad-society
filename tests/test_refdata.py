from ans import refdata


def test_loads_and_validates() -> None:
    data = refdata.load()
    assert len(data.countries) > 150
    assert len(data.cities) > 400
    assert data.images


def test_choice_lists_match_legacy_format() -> None:
    departures = refdata.departure_choices()
    assert all(" | " in choice for choice in departures)
    assert len(refdata.country_choices()) == len(refdata.load().countries)
