from datetime import date

from src.models.flights import SearchQuery
from src.services.providers import OriginRouter
from src.services.refdata import City
from tests.conftest import deal
from tests.fakes import FakeProvider


def query(origin_iata: str) -> SearchQuery:
    return SearchQuery(
        origin_iata=origin_iata,
        destination_iata="FI",
        date_from=date(2026, 9, 1),
        date_to=date(2026, 10, 1),
        min_nights=3,
        max_nights=7,
        currency="EUR",
    )


def test_router_searches_only_the_providers_an_origin_lists() -> None:
    tequila = FakeProvider({("MUC", "FI"): [deal()], ("FMM", "FI"): [deal()]})
    other = FakeProvider({("MUC", "FI"): [deal(price=99)]})
    router = OriginRouter(
        {"tequila": tequila, "other": other},
        [
            City(city="Munich", code="MUC", providers=["tequila", "other"]),
            City(city="Memmingen", code="FMM", providers=["tequila"]),
        ],
    )
    # Both providers' candidates come back for a shared origin.
    assert len(router.search_top(query("MUC"), 5)) == 2
    assert len(router.search_top(query("FMM"), 5)) == 1
    assert [q.origin_iata for q in other.queries] == ["MUC"]
