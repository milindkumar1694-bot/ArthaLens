from app.schemas.options import OptionChain

def ratio(numerator: int, denominator: int) -> float | None: return round(numerator / denominator, 4) if denominator else None
def calculate_pcr(chain: OptionChain, strike_range: int | None = None) -> dict[str, float | None]:
    rows = chain.strikes
    if strike_range is not None and chain.atm_strike is not None: rows = [r for r in rows if abs(r.strike-chain.atm_strike) <= strike_range]
    call_oi, put_oi = sum((r.ce.oi or 0) for r in rows if r.ce), sum((r.pe.oi or 0) for r in rows if r.pe)
    call_vol, put_vol = sum((r.ce.volume or 0) for r in rows if r.ce), sum((r.pe.volume or 0) for r in rows if r.pe)
    return {"oi": ratio(put_oi, call_oi), "volume": ratio(put_vol, call_vol)}
