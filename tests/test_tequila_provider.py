from datetime import date, datetime, timezone
from typing import Any

from src.app.models.flights import SearchQuery
from src.app.services.providers import FlightProvider
from src.app.services.providers.tequila import TequilaProvider
from tests.fakes import ResponseStub

QUERY = SearchQuery(
    origin_iata="FRA",
    destination_iata="HEL",
    date_from=date(2026, 9, 1),
    date_to=date(2026, 10, 1),
    min_nights=3,
    max_nights=7,
    currency="EUR",
)


def itinerary(
    itinerary_id: str, route: list[dict[str, Any]], price: float = 129.99
) -> dict[str, Any]:
    return {
        "id": itinerary_id,
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


def ts(day: int, hour: int = 12) -> int:
    """Tequila encodes local wall time as a UTC epoch."""
    return int(datetime(2026, 9, day, hour, tzinfo=timezone.utc).timestamp())


def leg(city: str, iata: str, day: int, hour: int, ret: int) -> dict[str, Any]:
    return {
        "flyTo": iata,
        "cityTo": city,
        "dTime": ts(day, hour),
        "aTime": ts(day, hour),
        "return": ret,
    }


DIRECT = itinerary(
    "d1",
    [leg("Helsinki", "HEL", 3, 10, 0), leg("Frankfurt", "FRA", 8, 18, 1)],
    price=149.99,
)
WITH_STOPS = itinerary(
    "s1",
    [
        leg("Riga", "RIX", 3, 6, 0),
        leg("Helsinki", "HEL", 3, 11, 0),
        leg("Oslo", "OSL", 9, 20, 1),
        leg("Frankfurt", "FRA", 9, 23, 1),
    ],
)


def test_direct_flight_maps_fields_timezone_fixed(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.services.providers.tequila.httpx2.Client.get",
        lambda self, *a, **k: ResponseStub({"data": [DIRECT]}),
    )
    provider: FlightProvider = TequilaProvider("https://t", "key")
    deals = provider.search_top(QUERY, 10)
    # The same itinerary comes back in both stopover passes and dedupes by id.
    assert len(deals) == 1
    deal = deals[0]
    assert deal.price == 149.99
    assert deal.arrival_country == "Finland"
    # Wall times survive regardless of the host timezone.
    assert deal.departs_at == datetime(2026, 9, 3, 10, 0)
    assert deal.returns_at == datetime(2026, 9, 8, 18, 0)
    assert deal.duration_minutes == 155
    assert deal.via_cities == []
    assert deal.return_via_cities == []


def test_direct_pass_precedes_stopover_pass(monkeypatch) -> None:
    captured: list[dict[str, Any]] = []

    def fake_get(self, url: str, params: dict[str, Any], **kwargs: Any) -> ResponseStub:
        captured.append(params)
        if params["max_sector_stopovers"] == 0:
            return ResponseStub({"data": [DIRECT]})
        return ResponseStub({"data": [WITH_STOPS, DIRECT]})

    monkeypatch.setattr(
        "src.app.services.providers.tequila.httpx2.Client.get", fake_get
    )
    deals = TequilaProvider("https://t", "key").search_top(QUERY, 10)
    assert [p["max_sector_stopovers"] for p in captured] == [0, 1]
    assert all(p["one_for_city"] == 1 and p["limit"] == 10 for p in captured)
    assert len(deals) == 2  # DIRECT appears in both passes, deduped by id
    by_id = {d.price: d for d in deals}
    stopover = by_id[129.99]
    assert stopover.via_cities == ["Riga"]
    assert stopover.return_via_cities == ["Oslo"]


def test_rate_limited_then_empty_returns_no_deals(monkeypatch) -> None:
    monkeypatch.setattr("src.app.services.providers.tequila.time.sleep", lambda s: None)
    monkeypatch.setattr(
        "src.app.services.providers.tequila.httpx2.Client.get",
        lambda self, *a, **k: ResponseStub({"error": "rate limited"}, status_code=429),
    )
    assert TequilaProvider("https://t", "key").search_top(QUERY, 10) == []


def test_pacing_kicks_in_only_at_the_quota(monkeypatch) -> None:
    from src.app.services.providers.tequila import RATE_LIMIT_PER_MINUTE

    provider = TequilaProvider("https://t", "key")
    slept: list[float] = []
    clock = {"now": 1000.0}
    monkeypatch.setattr(
        "src.app.services.providers.tequila.time.monotonic", lambda: clock["now"]
    )
    monkeypatch.setattr(
        "src.app.services.providers.tequila.time.sleep",
        lambda seconds: slept.append(seconds),
    )
    # A burst up to the quota runs unthrottled.
    for _ in range(RATE_LIMIT_PER_MINUTE):
        provider._pace()
    assert slept == []
    # The next request waits out the rest of the oldest request's minute.
    clock["now"] = 1010.0
    provider._pace()
    assert slept == [50.0]
    # A minute later the window is clear again.
    clock["now"] = 1100.0
    provider._pace()
    assert slept == [50.0]
