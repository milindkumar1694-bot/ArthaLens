from datetime import date
from app.data.normalizers.options import normalize_option_chain

def test_chain_normalizer_combines_legs_and_marks_bad_rows_partial():
    chain = normalize_option_chain([
        {"strike": 100, "option_type": "CE", "oi": 2, "volume": 1, "ltp": 3},
        {"strike": 100, "option_type": "PE", "oi": 4, "volume": 2, "ltp": 5},
        {"strike": -1, "option_type": "CE"},
    ], symbol="NIFTY", expiry=date(2027, 1, 1), source="test", underlying_price=101)
    assert chain.atm_strike == 100 and chain.strikes[0].ce.oi == 2 and chain.status == "partial"
