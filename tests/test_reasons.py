import json
from datetime import date

import pytest
import requests

import src.app.services.reasons as reasons_module
from src.app.config import Settings, get_settings
from src.app.models.flights import RankedDeal
from src.app.services.digest import DigestResult
from src.app.services.reasons import deal_reasons
from tests.conftest import deal
from tests.test_digest import SUBSCRIBER


class FakeResponse:
    def __init__(self, content: str, error: Exception | None = None):
        self.content = content
        self.error = error

    def raise_for_status(self) -> None:
        if self.error:
            raise self.error

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self.content}}]}


def digest() -> DigestResult:
    winner = RankedDeal(deal=deal(), source="favorite", score=150.0)
    runner_up = RankedDeal(deal=deal(price=115, via_cities=["Riga"]), source="favorite", score=160.0)
    return DigestResult(
        deals=[winner],
        runner_ups={"HEL": [runner_up]},
        window_start=date(2026, 9, 1),
        window_end=date(2026, 9, 30),
    )


def configured() -> Settings:
    return get_settings().model_copy(update={"ai_api_key": "test-ai-key"})


def reasons_with_response(monkeypatch, response: FakeResponse) -> dict[str, str]:
    calls: list[dict] = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return response

    monkeypatch.setattr(reasons_module.requests, "post", fake_post)
    result = deal_reasons(SUBSCRIBER, digest(), {"HEL": 310.0}, configured())
    if calls:
        body = calls[0]["json"]
        payload = json.loads(body["messages"][1]["content"])
        assert body["model"] == "claude-sonnet-5"
        assert calls[0]["url"] == "https://api.anthropic.com/v1/chat/completions"
        assert payload["deals"][0]["typical_price"] == 310.0
        assert payload["deals"][0]["beat_these_runner_ups"]
    return result


def test_no_key_skips_the_call(monkeypatch) -> None:
    def explode(*a, **k):
        raise AssertionError("must not call the API without a key")

    monkeypatch.setattr(reasons_module.requests, "post", explode)
    assert deal_reasons(SUBSCRIBER, digest(), {}, get_settings()) == {}


def test_reasons_parsed_from_response(monkeypatch) -> None:
    response = FakeResponse('{"HEL": "Direct at 10:40, no red-eye."}')
    assert reasons_with_response(monkeypatch, response) == {
        "HEL": "Direct at 10:40, no red-eye."
    }


def test_fenced_json_is_unwrapped(monkeypatch) -> None:
    response = FakeResponse('```json\n{"HEL": "Cheapest direct."}\n```')
    assert reasons_with_response(monkeypatch, response) == {"HEL": "Cheapest direct."}


def test_http_error_yields_no_reasons(monkeypatch) -> None:
    response = FakeResponse("", error=requests.HTTPError("500"))
    assert reasons_with_response(monkeypatch, response) == {}


def test_garbage_content_yields_no_reasons(monkeypatch) -> None:
    assert reasons_with_response(monkeypatch, FakeResponse("sorry, no JSON")) == {}


def test_non_string_reasons_are_dropped(monkeypatch) -> None:
    response = FakeResponse('{"HEL": 5, "TKU": "fine"}')
    assert reasons_with_response(monkeypatch, response) == {"TKU": "fine"}
