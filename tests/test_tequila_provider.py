from datetime import date, datetime
from typing import Any

from src.app.models.flights import SearchQuery
from src.app.services.providers import FlightProvider
from src.app.services.providers.tequila import TequilaProvider

QUERY = SearchQuery(
    origin_iata="FRA",
    destination_iata="HEL",
    date_from=date(2026, 9, 1),
    date_to=date(2026, 10, 1),
    min_nights=3,
    max_nights=7,
    currency="EUR",
)


def itinerary(route: list[dict[str, Any]], price: float = 129.99) -> dict[str, Any]:
    return {
        "price": price,
        "cityFrom": "Frankfurt",
        "flyFrom": "FRA",
        "cityTo": "Helsinki",
        "flyTo": "HEL",
        "countryTo": {"name": "Finland"},
        "deep_link": "https://kiwi.com/deep",
        "duration": {"departure": 9300},
        "route": route,
    }


class ResponseStub:
    def __init__(self, body: dict[str, Any], status_code: int = 200) -> None:
        self.body = body
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self.body


def ts(day: int, hour: int = 12) -> int:
    return int(datetime(2026, 9, day, hour, 0).timestamp())


def test_direct_flight_maps_fields(monkeypatch) -> None:
    direct = itinerary(
        [
            {"flyTo": "HEL", "cityTo": "Helsinki", "dTime": ts(3, 10), "aTime": ts(3)},
            {"flyTo": "FRA", "cityTo": "Frankfurt", "dTime": ts(8), "aTime": ts(8, 18)},
        ]
    )
    monkeypatch.setattr(
        "src.app.services.providers.tequila.requests.Session.get",
        lambda self, *a, **k: ResponseStub({"data": [direct]}),
    )
    provider: FlightProvider = TequilaProvider("https://t", "key")
    deals = provider.search_top(QUERY, 10)
    assert len(deals) == 1
    deal = deals[0]
    assert deal.price == 129.99
    assert deal.arrival_country == "Finland"
    assert deal.departs_at == datetime(2026, 9, 3, 10, 0)
    assert deal.returns_at == datetime(2026, 9, 8, 18, 0)
    assert deal.duration_minutes == 155
    assert deal.stopovers == 0
    assert deal.via_city is None


def test_single_search_returns_candidates_with_via_city(monkeypatch) -> None:
    with_stop = itinerary(
        [
            {"flyTo": "RIX", "cityTo": "Riga", "dTime": ts(3), "aTime": ts(3)},
            {"flyTo": "HEL", "cityTo": "Helsinki", "dTime": ts(3), "aTime": ts(3)},
            {"flyTo": "FRA", "cityTo": "Frankfurt", "dTime": ts(9), "aTime": ts(9)},
        ]
    )
    direct = itinerary(
        [
            {"flyTo": "HEL", "cityTo": "Helsinki", "dTime": ts(3), "aTime": ts(3)},
            {"flyTo": "FRA", "cityTo": "Frankfurt", "dTime": ts(9), "aTime": ts(9)},
        ],
        price=149.99,
    )
    captured: list[dict[str, Any]] = []

    def fake_get(self, url: str, params: dict[str, Any], **kwargs: Any) -> ResponseStub:
        captured.append(params)
        return ResponseStub({"data": [with_stop, direct]})

    monkeypatch.setattr(
        "src.app.services.providers.tequila.requests.Session.get", fake_get
    )
    deals = TequilaProvider("https://t", "key").search_top(QUERY, 10)
    assert len(captured) == 1
    assert captured[0]["max_sector_stopovers"] == 1
    assert captured[0]["limit"] == 10
    assert [d.via_city for d in deals] == ["Riga", None]
    assert [d.stopovers for d in deals] == [1, 0]


def test_rate_limited_then_empty_returns_no_deals(monkeypatch) -> None:
    monkeypatch.setattr("src.app.services.providers.tequila.time.sleep", lambda s: None)
    monkeypatch.setattr(
        "src.app.services.providers.tequila.requests.Session.get",
        lambda self, *a, **k: ResponseStub({"error": "rate limited"}, status_code=429),
    )
    assert TequilaProvider("https://t", "key").search_top(QUERY, 10) == []
