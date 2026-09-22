from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .common import Status


class MarketSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str
    exchange: str | None = None
    last_price: float | None = None
    change: float | None = None
    change_percent: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    previous_close: float | None = None
    volume: int | None = None
    timestamp: datetime
    source: str
    status: Status
    is_stale: bool = False
    message: str | None = None
    market_status: str = "UNKNOWN"
