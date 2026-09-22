from datetime import datetime, timezone
from typing import Mapping
from app.schemas.common import Status
from app.schemas.market import MarketSnapshot


def normalize_quote(raw: Mapping[str, object], *, source: str) -> MarketSnapshot:
    """Normalize a basic provider quote mapping, preserving absent values as null."""
    def number(name: str) -> float | None:
        value = raw.get(name)
        return float(value) if value is not None else None
    timestamp = raw.get("timestamp")
    if not isinstance(timestamp, datetime): timestamp = datetime.now(timezone.utc)
    return MarketSnapshot(symbol=str(raw["symbol"]).upper(), exchange=str(raw["exchange"]) if raw.get("exchange") else None,
        last_price=number("last_price"), change=number("change"), change_percent=number("change_percent"),
        open=number("open"), high=number("high"), low=number("low"), previous_close=number("previous_close"),
        volume=int(raw["volume"]) if raw.get("volume") is not None else None, timestamp=timestamp,
        source=source, status=Status.OK, message=None)
