from datetime import datetime, timezone
from app.schemas.options import OptionChain

def calculate_expiry(chain: OptionChain, max_pain: float | None) -> dict:
    if not chain.expiry: return {"days": None, "hours": None, "implied_move": None, "reason": "expiry unavailable"}
    delta = datetime.combine(chain.expiry, datetime.max.time(), tzinfo=timezone.utc)-datetime.now(timezone.utc); days = max(0, delta.total_seconds()/86400)
    atm = next((x for x in chain.strikes if x.strike == chain.atm_strike), None); move = (atm.ce.ltp or 0)+(atm.pe.ltp or 0) if atm and atm.ce and atm.pe and atm.ce.ltp is not None and atm.pe.ltp is not None else None
    return {"days": round(days, 3), "hours": round(max(0, delta.total_seconds()/3600), 2), "implied_move": move, "max_pain_distance": round(chain.underlying_price-max_pain, 2) if chain.underlying_price is not None and max_pain is not None else None, "label": "Market-implied move from ATM straddle; not a forecast."}
