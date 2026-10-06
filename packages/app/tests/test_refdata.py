"""Invariants of `packages/app/src/data.json` that the code relies on."""

from src.services import refdata


def test_images_are_queryable_with_no_orphan_keys() -> None:
    """No dead keys — and every URL carries a query string, which
    country_images' plain-& join relies on. Synced countries without
    images fall back to FALLBACK_IMAGE."""
    data = refdata.load()
    countries = {entry.country for entry in data.countries}
    assert set(data.images) - countries == set()
    for country, urls in data.images.items():
        assert urls, country
        assert all(url.startswith("https://") and "?" in url for url in urls), country
