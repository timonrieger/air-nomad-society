"""Invariants of `packages/app/src/data.json` that the code relies on."""

from src.services import refdata


def test_every_country_has_queryable_images_and_no_orphan_keys() -> None:
    """Commissioned in #37: full image coverage, no dead keys — and every
    URL carries a query string, which country_images' plain-& join relies on."""
    data = refdata.load()
    countries = {entry.country for entry in data.countries}
    assert countries - set(data.images) == set()
    assert set(data.images) - countries == set()
    for country, urls in data.images.items():
        assert urls, country
        assert all(url.startswith("https://") and "?" in url for url in urls), country
