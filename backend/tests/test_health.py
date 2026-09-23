from fastapi.testclient import TestClient
from app.main import app

def test_health_has_safe_optional_infrastructure_status():
    with TestClient(app) as client: response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "arthalens-api"
    assert "broker_authentication" in body["checks"]
    assert "redis_connectivity" in body["checks"]
