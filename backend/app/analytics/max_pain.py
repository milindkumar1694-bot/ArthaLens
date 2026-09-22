from app.schemas.options import OptionChain

def calculate_max_pain(chain: OptionChain) -> dict:
    strikes = [row.strike for row in chain.strikes]
    if not strikes: return {"strike": None, "candidate_strikes": [], "reason": "option chain unavailable"}
    payouts = []
    for candidate in strikes:
        payout = sum(max(0, candidate-row.strike)*(row.ce.oi or 0) + max(0, row.strike-candidate)*(row.pe.oi or 0) for row in chain.strikes)
        payouts.append({"strike": candidate, "payout": payout})
    return {"strike": min(payouts, key=lambda row: row["payout"])["strike"], "candidate_strikes": payouts, "reason": "Minimum aggregate intrinsic payout across supplied strikes; descriptive, not predictive."}
