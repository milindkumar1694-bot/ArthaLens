from app.data.normalizers.market import normalize_quote

def test_normalizer_preserves_missing_values_as_null():
    snapshot = normalize_quote({"symbol": "nifty", "last_price": 123.4}, source="broker_test")
    assert snapshot.symbol == "NIFTY" and snapshot.volume is None and snapshot.source == "broker_test"
