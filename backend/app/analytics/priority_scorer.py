from typing import Literal

PriorityTier = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]

def calculate_priority_score(
    spot_proximity: float,      # 0 to 100
    oi_change: float,           # 0 to 100
    iv_change: float,           # 0 to 100
    volume_spike: float,        # 0 to 100
    pcr_contribution: float,    # 0 to 100
    max_pain_proximity: float,  # 0 to 100
    news_relevance: float,      # 0 to 100
    days_to_expiry_factor: float, # 0 to 100
    round_number_bonus: float,  # 0 to 100
    historical_sr_bonus: float  # 0 to 100
) -> dict:
    score = (
        (spot_proximity * 0.25) +
        (oi_change * 0.20) +
        (iv_change * 0.15) +
        (volume_spike * 0.10) +
        (pcr_contribution * 0.10) +
        (max_pain_proximity * 0.05) +
        (news_relevance * 0.05) +
        (days_to_expiry_factor * 0.05) +
        (round_number_bonus * 0.03) +
        (historical_sr_bonus * 0.02)
    )
    score = round(min(100.0, max(0.0, score)), 2)

    if score > 80:
        tier: PriorityTier = "CRITICAL"
    elif score >= 60:
        tier = "HIGH"
    elif score >= 40:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return {
        "score": score,
        "tier": tier,
        "factors": {
            "spot_proximity": round(spot_proximity, 2),
            "oi_change": round(oi_change, 2),
            "iv_change": round(iv_change, 2),
            "volume_spike": round(volume_spike, 2),
            "pcr_contribution": round(pcr_contribution, 2),
            "max_pain_proximity": round(max_pain_proximity, 2),
            "news_relevance": round(news_relevance, 2),
            "days_to_expiry_factor": round(days_to_expiry_factor, 2),
            "round_number_bonus": round(round_number_bonus, 2),
            "historical_sr_bonus": round(historical_sr_bonus, 2)
        }
    }
