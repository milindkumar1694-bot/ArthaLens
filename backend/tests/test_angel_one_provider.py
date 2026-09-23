from datetime import date

import httpx
import pytest

from app.config.settings import Settings
from app.data.brokers.angel_one import AngelOneBrokerProvider
from app.schemas.common import Status
from app.services.cache import Cache
from app.services.market import MarketDataService


class StubAsyncClient:
    def __init__(self, post_handler, get_handler):
        self._post_handler = post_handler
        self._get_handler = get_handler

    async def post(self, url, **kwargs):
        return self._post_handler(url, **kwargs)

    async def get(self, url, **kwargs):
        return self._get_handler(url, **kwargs)

    async def aclose(self):
        return None


def _live_settings(**overrides):
    base = {
        "DATA_MODE": "live",
        "BROKER_PROVIDER": "angelone",
        "ANGEL_ONE_API_KEY": "api_key",
        "ANGEL_ONE_CLIENT_ID": "client_id",
        "ANGEL_ONE_PASSWORD": "password",
        "ANGEL_ONE_TOTP": "123456",
        "ANGEL_ONE_INSTRUMENT_MASTER_URL": "https://example.com/master.json",
    }
    base.update(overrides)
    return Settings(**base)


@pytest.mark.asyncio
async def test_market_service_initializes_angel_provider_in_live_mode():
    service = MarketDataService(_live_settings(), Cache())
    status = await service.provider_status()
    assert status.provider == "angelone"
    assert status.configured is True


@pytest.mark.asyncio
async def test_angel_one_missing_credentials_marks_provider_unavailable():
    settings = Settings(DATA_MODE="live", BROKER_PROVIDER="angelone", ANGEL_ONE_API_KEY="", ANGEL_ONE_CLIENT_ID="")
    provider = AngelOneBrokerProvider(settings)

    await provider.connect()
    status = await provider.status()

    assert provider.connected is False
    assert status.configured is False
    assert status.status == Status.UNAVAILABLE


@pytest.mark.asyncio
async def test_angel_one_authentication_success(monkeypatch):
    provider = AngelOneBrokerProvider(_live_settings())

    def post_handler(url, **kwargs):
        if url.endswith("loginByPassword"):
            return httpx.Response(200, json={"status": True, "data": {"jwtToken": "jwt", "feedToken": "feed"}})
        raise AssertionError("unexpected POST")

    def get_handler(url, **kwargs):
        return httpx.Response(200, json=[])

    provider._http_client = StubAsyncClient(post_handler=post_handler, get_handler=get_handler)

    await provider.connect()
    status = await provider.status()

    assert provider.connected is True
    assert provider.jwt_token == "jwt"
    assert provider.feed_token == "feed"
    assert status.status == Status.OK


@pytest.mark.asyncio
async def test_angel_one_authentication_failure(monkeypatch):
    provider = AngelOneBrokerProvider(_live_settings())

    def post_handler(url, **kwargs):
        return httpx.Response(401, json={"status": False, "errorcode": "AB1010", "message": "Invalid totp"})

    def get_handler(url, **kwargs):
        return httpx.Response(200, json=[])

    provider._http_client = StubAsyncClient(post_handler=post_handler, get_handler=get_handler)

    await provider.connect()

    assert provider.connected is False
    assert provider.jwt_token is None
    assert provider.last_auth_reason == "authentication_failed"
    assert provider.last_auth_http_status == 401


@pytest.mark.asyncio
async def test_nifty_and_banknifty_quote_mapping_uses_instrument_master():
    provider = AngelOneBrokerProvider(_live_settings())
    payloads = []

    instruments = [
        {"exch_seg": "NSE", "symbol": "Nifty 50", "name": "NIFTY", "token": "99926000"},
        {"exch_seg": "NSE", "symbol": "Nifty Bank", "name": "BANKNIFTY", "token": "99926009"},
    ]

    def post_handler(url, **kwargs):
        if url.endswith("loginByPassword"):
            return httpx.Response(200, json={"status": True, "data": {"jwtToken": "jwt", "feedToken": "feed"}})
        payload = kwargs["json"]
        payloads.append(payload)
        ltp = 25000 if payload["symboltoken"] == "99926000" else 51000
        return httpx.Response(200, json={"status": True, "data": {"ltp": ltp, "close": ltp - 100}})

    def get_handler(url, **kwargs):
        return httpx.Response(200, json=instruments)

    provider._http_client = StubAsyncClient(post_handler=post_handler, get_handler=get_handler)
    await provider.connect()

    nifty = await provider.get_quote("NIFTY")
    banknifty = await provider.get_quote("BANKNIFTY")

    assert nifty.status == Status.OK
    assert banknifty.status == Status.OK
    assert payloads[0]["tradingsymbol"] == "Nifty 50"
    assert payloads[0]["symboltoken"] == "99926000"
    assert payloads[1]["tradingsymbol"] == "Nifty Bank"
    assert payloads[1]["symboltoken"] == "99926009"


@pytest.mark.asyncio
async def test_expiry_retrieval_uses_metadata_dates():
    provider = AngelOneBrokerProvider(_live_settings())
    rows = [
        {"exch_seg": "NFO", "instrumenttype": "OPTIDX", "symbol": "NIFTY26SEP2026CE", "name": "NIFTY", "expiry": "26SEP2026", "strike": "2500000", "token": "1", "lotsize": "50"},
        {"exch_seg": "NFO", "instrumenttype": "OPTIDX", "symbol": "NIFTY03OCT2026CE", "name": "NIFTY", "expiry": "03OCT2026", "strike": "2510000", "token": "2", "lotsize": "50"},
    ]

    provider._http_client = StubAsyncClient(
        post_handler=lambda *args, **kwargs: httpx.Response(200, json={"status": True, "data": {"jwtToken": "jwt", "feedToken": "feed"}}),
        get_handler=lambda *args, **kwargs: httpx.Response(200, json=rows),
    )

    info = await provider.get_expiries("NIFTY")

    assert info.status == Status.OK
    assert info.expiries == [date(2026, 9, 26), date(2026, 10, 3)]
    assert info.nearest_expiry == date(2026, 9, 26)


@pytest.mark.asyncio
async def test_option_instrument_parsing_for_nifty_contracts():
    provider = AngelOneBrokerProvider(_live_settings())
    rows = [
        {"exch_seg": "NFO", "instrumenttype": "OPTIDX", "symbol": "NIFTY26SEP202624500CE", "name": "NIFTY", "expiry": "26SEP2026", "strike": "2450000", "token": "11", "lotsize": "50"},
        {"exch_seg": "NFO", "instrumenttype": "OPTIDX", "symbol": "NIFTY26SEP202624500PE", "name": "NIFTY", "expiry": "26SEP2026", "strike": "2450000", "token": "12", "lotsize": "50"},
    ]

    provider._http_client = StubAsyncClient(
        post_handler=lambda *args, **kwargs: httpx.Response(200, json={"status": True}),
        get_handler=lambda *args, **kwargs: httpx.Response(200, json=rows),
    )

    instruments = await provider.get_instruments("NIFTY")

    assert len(instruments) == 2
    assert {item.option_type for item in instruments} == {"CE", "PE"}
    assert instruments[0].strike == 24500


@pytest.mark.asyncio
async def test_option_chain_returns_unavailable_when_not_connected():
    provider = AngelOneBrokerProvider(_live_settings())

    chain = await provider.get_option_chain("NIFTY")

    assert chain.status == Status.UNAVAILABLE
    assert chain.strikes == []
