from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel
from app.schemas.common import Status

ViolenceProbability = Literal["LOW", "MEDIUM", "HIGH"]
ExpiryRegime = Literal["Pinning", "Squeeze", "Neutral"]
CasStatus = Literal["NORMAL", "ELEVATED", "EXTREME", "UNAVAILABLE"]

class GammaStrikeProfile(BaseModel):
    strike: float
    gex: float
    is_pin_target: bool = False
    is_gamma_wall: bool = False

class DealerHedgingEstimate(BaseModel):
    net_gex: float
    dealer_position: Literal["Long Gamma", "Short Gamma", "Neutral"]
    hedging_direction: str  # e.g., "Sell Rallies / Buy Dips" (Long Gamma) or "Buy Rallies / Sell Dips" (Short Gamma)
    gamma_flip_level: float | None
    distance_to_flip: float | None

class ExpiryProbabilityScore(BaseModel):
    pinning_probability: float  # e.g. 65.0 %
    squeeze_probability: float  # e.g. 25.0 %
    breakout_probability: float  # e.g. 10.0 %
    primary_factor: str

class CasWindowMonitor(BaseModel):
    active_window: bool  # True between 3:15 PM and 3:40 PM IST
    indicative_close: float | None
    regular_close: float | None
    divergence_percent: float | None
    status: CasStatus
    alert_triggered: bool

class HistoricalExpiryPattern(BaseModel):
    date: date
    symbol: str
    net_gex_regime: ExpiryRegime
    violence_occurred: bool
    max_intraday_move_pts: float
    max_intraday_move_pct: float
    pin_target_hit: bool

class ExpiryIntelPayload(BaseModel):
    symbol: str
    expiry: date | None
    timestamp: datetime
    status: Status
    net_gex: float
    regime: ExpiryRegime
    violence_probability: ViolenceProbability
    pin_target_strike: float | None
    expected_range_lower: float | None
    expected_range_upper: float | None
    gamma_profile: list[GammaStrikeProfile]
    dealer_hedging: DealerHedgingEstimate
    probability_score: ExpiryProbabilityScore
    cas_monitor: CasWindowMonitor
    historical_comparison: list[HistoricalExpiryPattern]
    alerts: list[str] = []
    limitations_disclaimer: list[str] = [
        "GEX sign is estimated based on call/put OI proxies.",
        "Assumes dealers are net short options.",
        "Unexpected news shocks override gamma mechanics.",
        "CAS data may be delayed depending on market feed.",
        "Historical patterns are not guaranteed to repeat."
    ]
