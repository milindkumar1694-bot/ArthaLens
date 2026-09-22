from app.schemas.options import OptionChain

def calculate_oi_levels(chain: OptionChain) -> dict:
    spot = chain.underlying_price
    def rows(side: str, above: bool) -> list[dict]:
        values = []
        for row in chain.strikes:
            leg = getattr(row, side)
            if leg is None or leg.oi is None or spot is None or (row.strike >= spot) != above: continue
            distance = row.strike-spot
            strength = round(min(100, (leg.oi / max(1, max((getattr(x, side).oi or 0) for x in chain.strikes if getattr(x, side)))) * 70 + min(20, abs(leg.change_oi or 0)/max(1, leg.oi)*100) + min(10, (leg.volume or 0)/max(1, leg.oi)*100)), 2)
            values.append({"strike": row.strike, "oi": leg.oi, "change_oi": leg.change_oi, "volume": leg.volume, "distance_from_spot": round(distance, 2), "distance_percent": round(distance/spot*100, 3), "strength": strength})
        return sorted(values, key=lambda value: value["strength"], reverse=True)[:3]
    support, resistance = rows("pe", False), rows("ce", True)
    return {"support": support, "resistance": resistance, "nearest_support": min(support, key=lambda v: abs(v["distance_from_spot"]), default=None), "nearest_resistance": min(resistance, key=lambda v: abs(v["distance_from_spot"]), default=None), "methodology": "Strength: OI concentration 70%, relative change in OI 20%, volume/OI 10%. Positioning concentrations are not guaranteed levels."}
