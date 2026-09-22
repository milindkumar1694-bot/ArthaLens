import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app
from app.services.market import MarketDataService
from app.analytics.cas_monitor import check_cas_window
from app.analytics.news_fusion import analyze_news_fusion

client = TestClient(app)

@pytest.mark.asyncio
async def test_live_mode_never_returns_mock_quotes():
    service = MarketDataService(Settings(DATA_MODE="live", BROKER_PROVIDER="mock"))
    quote = await service.quote("NIFTY")
    assert quote.status == "unavailable"
    assert quote.source != "mock"
    assert quote.last_price is None
    assert "Live mode never falls back to mock data" in quote.message

def test_live_mode_cas_monitor_returns_unavailable_without_feed():
    cas = check_cas_window(spot_price=22540.25, indicative_close=None, is_live_mode=True)
    assert cas.status == "UNAVAILABLE"
    assert cas.indicative_close is None
    assert cas.divergence_percent is None
    assert cas.alert_triggered is False

def test_live_mode_news_returns_unavailable_without_feed():
    news_payload = analyze_news_fusion(chain=None, is_live_mode=True, live_news_items=None)
    assert news_payload.status == "unavailable"
    assert len(news_payload.items) == 0
    assert len(news_payload.fusion_insights) == 0

def test_health_endpoint_does_not_reveal_secrets():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    # Verify no secret values are leaked in checks payload
    for key, val in data["checks"].items():
        assert "sk-" not in str(val)
        assert "password" not in str(val).lower()
