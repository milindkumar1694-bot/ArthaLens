from app.analytics.greeks import calculate_greeks
from app.schemas.options import OptionChain

def get_lot_size(symbol: str) -> int:
    sym = (symbol or "").upper()
    if "BANK" in sym:
        return 15
    if "FIN" in sym:
        return 25
    return 50  # NIFTY default

def calculate_gex(chain: OptionChain, days: float, rate: float, lot_size: int | None = None) -> dict:
    if chain.underlying_price is None:
        return {
            "value": None,
            "sign": "unknown",
            "profile": [],
            "reason": "underlying price unavailable",
            "pin_target": None,
            "gamma_flip": None,
            "dealer_hedging": {"dealer_position": "Neutral", "hedging_direction": "Unknown"}
        }

    actual_lot = lot_size if lot_size and lot_size > 1 else get_lot_size(chain.symbol)
    profile = []

    for row in chain.strikes:
        ce = calculate_greeks(chain.underlying_price, row.strike, row.ce.iv if row.ce else None, days, True, rate)
        pe = calculate_greeks(chain.underlying_price, row.strike, row.pe.iv if row.pe else None, days, False, rate)
        
        ce_gamma = ce["gamma"] if ce and ce.get("gamma") is not None else 0.0
        pe_gamma = pe["gamma"] if pe and pe.get("gamma") is not None else 0.0

        ce_gex = ce_gamma * (row.ce.oi or 0) * actual_lot * chain.underlying_price * 0.01
        pe_gex = -1.0 * pe_gamma * (row.pe.oi or 0) * actual_lot * chain.underlying_price * 0.01
        net_strike_gex = ce_gex + pe_gex

        profile.append({
            "strike": row.strike,
            "gex": round(net_strike_gex, 2),
            "ce_gex": round(ce_gex, 2),
            "pe_gex": round(pe_gex, 2)
        })

    total = round(sum(item["gex"] for item in profile), 2)
    
    # Find pin target (highest positive GEX strike)
    positive_strikes = [p for p in profile if p["gex"] > 0]
    pin_target = max(positive_strikes, key=lambda x: x["gex"])["strike"] if positive_strikes else chain.atm_strike

    # Find Gamma flip level where profile crosses zero
    flip = next((right["strike"] for left, right in zip(profile, profile[1:]) if left["gex"] * right["gex"] < 0), None)
    if flip is None and profile:
        # fallback to strike nearest to spot if no zero crossing
        flip = min(profile, key=lambda x: abs(x["strike"] - chain.underlying_price))["strike"]

    # Dealer Hedging Estimate logic
    if total > 0:
        dealer_pos = "Long Gamma"
        hedging_dir = "Sell Rallies / Buy Dips (Dampening)"
        regime = "Pinning"
        violence_prob = "LOW"
    elif total < 0:
        dealer_pos = "Short Gamma"
        hedging_dir = "Buy Rallies / Sell Dips (Amplifying Squeeze)"
        regime = "Squeeze"
        violence_prob = "HIGH"
    else:
        dealer_pos = "Neutral"
        hedging_dir = "Balanced Flows"
        regime = "Neutral"
        violence_prob = "MEDIUM"

    dist_flip = round(chain.underlying_price - flip, 2) if flip and chain.underlying_price else None

    return {
        "value": total,
        "sign": "positive" if total > 0 else "negative" if total < 0 else "neutral",
        "regime": regime,
        "violence_probability": violence_prob,
        "profile": profile,
        "gamma_flip": flip,
        "pin_target": pin_target,
        "distance_to_flip": dist_flip,
        "dealer_hedging": {
            "net_gex": total,
            "dealer_position": dealer_pos,
            "hedging_direction": hedging_dir,
            "gamma_flip_level": flip,
            "distance_to_flip": dist_flip
        },
        "confidence": "Medium",
        "assumptions": [
            "Black-Scholes gamma model estimation.",
            "Call OI positive / put OI negative dealer-position proxy.",
            "Market maker positioning inferred from open interest."
        ]
    }
