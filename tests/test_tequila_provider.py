from datetime import UTC, date, datetime
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


def itinerary(route: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "price": 129.99,
        "cityFrom": "Frankfurt",
        "flyFrom": "FRA",
        "cityTo": "Helsinki",
        "flyTo": "HEL",
        "countryTo": {"name": "Finland"},
        "deep_link": "https://kiwi.com/deep",
        "route": route,
    }


class ResponseStub:
    def __init__(self, body: dict[str, Any], status_code: int = 200) -> None:
        self.body = body
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self.body


def ts(day: int) -> int:
    # Tequila-style timestamp: local wall-clock time encoded as a UTC epoch.
    return int(datetime(2026, 9, day, 12, 0, tzinfo=UTC).timestamp())


def test_direct_flight_maps_fields(monkeypatch) -> None:
    direct = itinerary(
        [
            {"flyTo": "HEL", "cityTo": "Helsinki", "dTime": ts(3), "aTime": ts(3)},
            {"flyTo": "FRA", "cityTo": "Frankfurt", "dTime": ts(8), "aTime": ts(8)},
        ]
    )
    monkeypatch.setattr(
        "src.app.services.providers.tequila.requests.Session.get",
        lambda self, *a, **k: ResponseStub({"data": [direct]}),
    )
    provider: FlightProvider = TequilaProvider("https://t", "key")
    deal = provider.search_cheapest(QUERY)
    assert deal is not None
    assert deal.price == 129.99
    assert deal.arrival_country == "Finland"
    assert deal.departs_on == date(2026, 9, 3)
    assert deal.returns_on == date(2026, 9, 8)
    assert deal.via_city is None


def test_stopover_escalation_and_via_city(monkeypatch) -> None:
    with_stop = itinerary(
        [
            {"flyTo": "RIX", "cityTo": "Riga", "dTime": ts(3), "aTime": ts(3)},
            {"flyTo": "HEL", "cityTo": "Helsinki", "dTime": ts(3), "aTime": ts(3)},
            {"flyTo": "FRA", "cityTo": "Frankfurt", "dTime": ts(9), "aTime": ts(9)},
        ]
    )
    calls: list[int] = []

    def fake_get(self, url: str, params: dict[str, Any], **kwargs: Any) -> ResponseStub:
        calls.append(params["max_sector_stopovers"])
        if params["max_sector_stopovers"] == 0:
            return ResponseStub({"data": []})
        return ResponseStub({"data": [with_stop]})

    monkeypatch.setattr(
        "src.app.services.providers.tequila.requests.Session.get", fake_get
    )
    deal = TequilaProvider("https://t", "key").search_cheapest(QUERY)
    assert calls == [0, 1]
    assert deal is not None
    assert deal.via_city == "Riga"
    assert deal.returns_on == date(2026, 9, 9)


def test_rate_limited_then_empty_returns_none(monkeypatch) -> None:
    monkeypatch.setattr("src.app.services.providers.tequila.time.sleep", lambda s: None)
    monkeypatch.setattr(
        "src.app.services.providers.tequila.requests.Session.get",
        lambda self, *a, **k: ResponseStub({"error": "rate limited"}, status_code=429),
    )
    assert TequilaProvider("https://t", "key").search_cheapest(QUERY) is None
