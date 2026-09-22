from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from app.schemas.common import Status

PriorityTier = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]

class ScoreFactorBreakdown(BaseModel):
    spot_proximity: float
    oi_change: float
    iv_change: float
    volume_spike: float
    pcr_contribution: float
    max_pain_proximity: float
    news_relevance: float
    days_to_expiry_factor: float
    round_number_bonus: float
    historical_sr_bonus: float

class WatchlistItem(BaseModel):
    rank: int
    asset: str
    event_or_driver: str
    reason: str
    priority_score: float  # 0 to 100
    priority_tier: PriorityTier
    confidence: Literal["High", "Medium", "Low"]
    direction: Literal["Positive", "Negative", "Mixed", "Neutral"]
    factors: ScoreFactorBreakdown
    trade_hint: str
    timestamp: datetime

class WatchlistPayload(BaseModel):
    timestamp: datetime
    status: Status
    universe: list[str]
    items: list[WatchlistItem]
