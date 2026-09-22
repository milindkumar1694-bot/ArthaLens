from fastapi.testclient import TestClient
from app.main import app

def test_expiry_and_option_chain_pipeline():
    with TestClient(app) as client:
        expiries = client.get("/api/v1/options/expiries?symbol=NIFTY")
        chain = client.get("/api/v1/options/nifty")
    assert expiries.status_code == 200 and expiries.json()["source"] == "mock"
    body = chain.json()
    assert chain.status_code == 200 and body["source"] == "mock" and body["atm_strike"] is not None
    assert body["strikes"][0]["ce"]["oi"] is not None and body["strikes"][0]["pe"]["ltp"] is not None

def test_strike_filtering_and_banknifty_chain():
    with TestClient(app) as client:
        filtered = client.get("/api/v1/options/NIFTY?strike_range=50").json()
        bank = client.get("/api/v1/options/BANKNIFTY").json()
    assert len(filtered["strikes"]) <= 3
    assert bank["symbol"] == "BANKNIFTY" and bank["atm_strike"] is not None
