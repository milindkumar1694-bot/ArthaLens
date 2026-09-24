import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.config import Settings
from app.data.brokers.angel_one import AngelOneBrokerProvider
from app.services.market import MarketDataService
from app.database.session import database_check
from app.services.cache import Cache
from app.main import app

@pytest.fixture
def live_settings():
    return Settings(
        DATA_MODE="live",
        BROKER_PROVIDER="angelone",
        ANGEL_ONE_API_KEY="mock_api_key",
        ANGEL_ONE_CLIENT_ID="mock_client_id",
        ANGEL_ONE_PASSWORD="mock_password",
        ANGEL_ONE_TOTP="mock_totp"
    )

@pytest.mark.asyncio
async def test_successful_startup_authentication(live_settings):
    provider = AngelOneBrokerProvider(live_settings)
    
    auth_response_data = {
        "status": True,
        "data": {
            "jwtToken": "mock_jwt_token_123",
            "feedToken": "mock_feed_token_456"
        }
    }
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = auth_response_data
    mock_post = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient.post", mock_post):
        await provider.connect()

    assert provider.connected is True
    assert provider.jwt_token == "mock_jwt_token_123"
    assert provider.feed_token == "mock_feed_token_456"
    assert provider.authenticated_at is not None

@pytest.mark.asyncio
async def test_provider_state_logging_and_single_instance(live_settings):
    service = MarketDataService(live_settings)
    provider1 = service.provider
    assert provider1 is not None
    assert isinstance(provider1, AngelOneBrokerProvider)
    
    # Verify same provider instance is retained
    assert service.provider is provider1
    
    # Check status without leaking sensitive data
    status = await service.provider_status()
    assert status.provider == "angelone"
    assert "mock_jwt_token_123" not in str(status)
    assert "mock_api_key" not in str(status)

@pytest.mark.asyncio
async def test_session_expiration_and_successful_reauthentication(live_settings):
    provider = AngelOneBrokerProvider(live_settings)
    provider.jwt_token = "expired_token"
    provider.feed_token = "expired_feed"
    provider.connected = True

    # 1st quote response returns session expired (HTTP 401)
    # connect() attempt returns new valid tokens
    # 2nd quote response returns valid quote data
    auth_response = {
        "status": True,
        "data": {
            "jwtToken": "new_jwt_token_789",
            "feedToken": "new_feed_token_012"
        }
    }
    quote_response = {
        "status": True,
        "data": {
            "ltp": 22550.0,
            "close": 22500.0
        }
    }

    call_count = 0

    async def mock_post_impl(url, **kwargs):
        nonlocal call_count
        mock_resp = MagicMock()
        if "loginByPassword" in url:
            mock_resp.status_code = 200
            mock_resp.json.return_value = auth_response
            return mock_resp
        elif "getLtpData" in url:
            call_count += 1
            if call_count == 1:
                mock_resp.status_code = 401
                mock_resp.json.return_value = {"status": False, "message": "Invalid token", "errorcode": "AG8001"}
                return mock_resp
            else:
                mock_resp.status_code = 200
                mock_resp.json.return_value = quote_response
                return mock_resp
        mock_resp.status_code = 404
        mock_resp.json.return_value = {}
        return mock_resp

    with patch("httpx.AsyncClient.post", side_effect=mock_post_impl):
        quote = await provider.get_quote("NIFTY")

    assert quote.status == "ok"
    assert quote.last_price == 22550.0
    assert provider.connected is True
    assert provider.jwt_token == "new_jwt_token_789"

@pytest.mark.asyncio
async def test_failed_reauthentication(live_settings):
    provider = AngelOneBrokerProvider(live_settings)
    provider.jwt_token = "invalid_token"
    provider.connected = True

    async def mock_post_impl(url, **kwargs):
        mock_resp = MagicMock()
        if "loginByPassword" in url:
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"status": False, "message": "Invalid TOTP"}
            return mock_resp
        else:
            mock_resp.status_code = 401
            mock_resp.json.return_value = {"status": False, "message": "Token expired"}
            return mock_resp

    with patch("httpx.AsyncClient.post", side_effect=mock_post_impl):
        quote = await provider.get_quote("NIFTY")

    assert quote.status == "unavailable"
    assert "re-authentication failed" in quote.message
    assert provider.connected is False
    assert provider.jwt_token is None

def test_database_health_check_status():
    assert database_check(None) == "not_configured"
    
    mock_engine_fail = MagicMock()
    mock_engine_fail.connect.side_effect = Exception("DB Connection Refused")
    assert database_check(mock_engine_fail) == "unavailable"

    mock_engine_ok = MagicMock()
    mock_connection = MagicMock()
    mock_engine_ok.connect.return_value.__enter__.return_value = mock_connection
    assert database_check(mock_engine_ok) == "ok"

@pytest.mark.asyncio
async def test_redis_health_check_status():
    cache_empty = Cache("")
    assert cache_empty.status == "not_configured"

    cache_bad = Cache("redis://localhost:9999/0")
    await cache_bad.connect()
    assert cache_bad.status == "unavailable"

def test_health_endpoint_response_accuracy():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "arthalens-api"
        checks = data["checks"]
        assert "application" in checks
        assert "broker_configuration" in checks
        assert "broker_authentication" in checks
        assert "broker_connectivity" in checks
        assert "redis_configuration" in checks
        assert "redis_connectivity" in checks
