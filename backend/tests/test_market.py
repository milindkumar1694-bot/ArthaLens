from fastapi.testclient import TestClient
import pytest
from datetime import datetime, timedelta, timezone
from app.main import app
from app.config.settings import Settings
from app.services.market import MarketDataService

def test_market_endpoint_returns_normalized_snapshot():
    with TestClient(app) as client: response = client.get("/api/v1/market/NIFTY")
    assert response.status_code == 200
    assert response.json()["source"] == "mock"

@pytest.mark.asyncio
async def test_live_mode_never_falls_back_to_mock():
    quote = await MarketDataService(Settings(DATA_MODE="live", BROKER_PROVIDER="mock")).quote("NIFTY")
    assert quote.status == "unavailable" and quote.source == "not_configured"

def test_stale_data_is_flagged_from_configured_threshold():
    service = MarketDataService(Settings(DATA_MODE="mock", BROKER_PROVIDER="mock", MAX_MARKET_DATA_AGE_SECONDS=1))
    quote = __import__("asyncio").run(service.quote("NIFTY")).model_copy(update={"timestamp": datetime.now(timezone.utc)-timedelta(seconds=2)})
    assert service._stale(quote, 1).is_stale is True
