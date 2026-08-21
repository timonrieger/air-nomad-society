import json

import src.app.services.reasons as reasons_module
from src.app.config import Settings, get_settings
from src.app.models.flights import RankedDeal
from src.app.services.reasons import deal_reasons
from tests.conftest import deal
from tests.fakes import ResponseStub
from tests.test_digest import SUBSCRIBER
from tests.test_emails import ranked


def picks() -> list[RankedDeal]:
    winner = ranked(deal())
    winner.runner_ups = [ranked(deal(price=115, via_cities=["Riga"]))]
    return [winner]


def configured() -> Settings:
    return get_settings().model_copy(update={"ai_api_key": "test-ai-key"})


def chat_response(content: str) -> ResponseStub:
    return ResponseStub({"choices": [{"message": {"content": content}}]})


def reasons_with_response(monkeypatch, response: ResponseStub) -> list[RankedDeal]:
    calls: list[dict] = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return response

    monkeypatch.setattr(reasons_module.requests, "post", fake_post)
    deals = picks()
    deal_reasons(SUBSCRIBER, deals, {"HEL": 310.0}, configured())
    body = calls[0]["json"]
    payload = json.loads(body["messages"][1]["content"])
    assert calls[0]["url"] == "https://api.anthropic.com/v1/chat/completions"
    assert body["model"] == "claude-sonnet-5"
    assert payload["deals"][0]["id"] == 0
    assert payload["deals"][0]["typical_price"] == 310.0
    assert payload["deals"][0]["beat_these_runner_ups"]
    return deals


def test_no_key_skips_the_call(monkeypatch) -> None:
    def explode(*a, **k):
        raise AssertionError("must not call the API without a key")

    monkeypatch.setattr(reasons_module.requests, "post", explode)
    deals = picks()
    deal_reasons(SUBSCRIBER, deals, {}, get_settings())
    assert deals[0].reason is None


def test_reasons_attached_from_response(monkeypatch) -> None:
    deals = reasons_with_response(
        monkeypatch, chat_response('{"0": "Direct at 10:40, no red-eye."}')
    )
    assert deals[0].reason == "Direct at 10:40, no red-eye."


def test_fenced_json_is_unwrapped(monkeypatch) -> None:
    deals = reasons_with_response(
        monkeypatch, chat_response('```json\n{"0": "Cheapest direct."}\n```')
    )
    assert deals[0].reason == "Cheapest direct."


def test_http_error_yields_no_reasons(monkeypatch) -> None:
    deals = reasons_with_response(monkeypatch, ResponseStub({}, status_code=500))
    assert deals[0].reason is None


def test_garbage_content_yields_no_reasons(monkeypatch) -> None:
    deals = reasons_with_response(monkeypatch, chat_response("sorry, no JSON"))
    assert deals[0].reason is None


def test_non_string_reasons_are_dropped(monkeypatch) -> None:
    deals = reasons_with_response(monkeypatch, chat_response('{"0": 5}'))
    assert deals[0].reason is None
