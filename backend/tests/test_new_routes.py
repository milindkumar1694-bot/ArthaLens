import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_expiry_route():
    response = client.get("/api/v1/expiry/NIFTY")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NIFTY"
    assert "net_gex" in data
    assert "regime" in data
    assert "gamma_profile" in data
    assert "dealer_hedging" in data
    assert "probability_score" in data

def test_news_route():
    response = client.get("/api/v1/news")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert "fusion_insights" in data

def test_watchlist_route():
    response = client.get("/api/v1/watchlist")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert "priority_score" in data["items"][0]
