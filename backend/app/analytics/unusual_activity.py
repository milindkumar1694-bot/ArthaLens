from app.schemas.options import OptionChain

def calculate_unusual_activity(chain: OptionChain) -> list[dict]:
    legs = [(row.strike, kind, getattr(row, kind)) for row in chain.strikes for kind in ("ce", "pe") if getattr(row, kind)]
    max_volume = max((leg.volume or 0 for _, _, leg in legs), default=0); max_change = max((abs(leg.change_oi or 0) for _, _, leg in legs), default=0)
    items = []
    for strike, kind, leg in legs:
        score = round(((leg.volume or 0)/max(1,max_volume)*60)+abs(leg.change_oi or 0)/max(1,max_change)*40, 2)
        if score >= 60: items.append({"strike": strike, "option_type": kind.upper(), "score": score, "volume": leg.volume, "change_oi": leg.change_oi, "reason": "Current-session volume and OI-change concentration; historical comparison unavailable."})
    return sorted(items, key=lambda item: item["score"], reverse=True)[:8]
