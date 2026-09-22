from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from app.schemas.common import Status

NewsImportance = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
NewsDirection = Literal["Positive", "Negative", "Mixed", "Neutral"]
IvImpact = Literal["Rising", "Falling", "Unchanged", "Crush"]
NewsCategory = Literal["RBI", "Budget", "Fed", "CPI", "Earnings", "FII_DII", "Geopolitical", "Crude_INR", "SEBI"]

class StrikeImpact(BaseModel):
    strike: float
    option_type: Literal["CE", "PE", "BOTH"]
    action: str  # e.g., "PE Buy / CE Write"

class NewsItem(BaseModel):
    id: str
    headline: str
    summary: str
    category: NewsCategory
    affected_asset: str
    direction: NewsDirection
    importance: NewsImportance
    iv_impact: IvImpact
    affected_strikes: list[StrikeImpact] = []
    expected_move_change: float = 0.0  # pts expansion/contraction
    why_it_matters: str
    what_to_watch_next: str
    confidence: Literal["High", "Medium", "Low"]
    timestamp: datetime
    source: str = "curated"

class NewsFusionResult(BaseModel):
    news_id: str
    headline: str
    news_bias: NewsDirection
    options_pricing_bias: NewsDirection
    aligned: bool
    status_label: Literal["Confirmation", "Divergence", "Neutral"]
    analysis: str
    confidence: Literal["High", "Medium", "Low"]

class NewsResponsePayload(BaseModel):
    timestamp: datetime
    status: Status
    categories: list[str]
    items: list[NewsItem]
    fusion_insights: list[NewsFusionResult]
