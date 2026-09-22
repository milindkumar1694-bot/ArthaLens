from datetime import date, datetime
from pydantic import BaseModel, Field
from .common import Status


class Instrument(BaseModel):
    symbol: str
    underlying: str
    exchange: str | None = None
    expiry: date | None = None
    strike: float | None = None
    option_type: str | None = None
    instrument_token: str | None = None
    trading_symbol: str | None = None
    lot_size: int | None = None
    provider: str


class OptionLeg(BaseModel):
    symbol: str | None = None
    oi: int | None = Field(default=None, ge=0)
    change_oi: int | None = None
    volume: int | None = Field(default=None, ge=0)
    iv: float | None = Field(default=None, ge=0)
    ltp: float | None = Field(default=None, ge=0)
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)


class OptionStrike(BaseModel):
    strike: float = Field(gt=0)
    ce: OptionLeg | None = None
    pe: OptionLeg | None = None

StrikeRow = OptionStrike


class ExpiryInfo(BaseModel):
    symbol: str
    expiries: list[date]
    nearest_expiry: date | None = None
    next_expiry: date | None = None
    monthly_expiry: date | None = None
    source: str
    timestamp: datetime
    status: Status
    is_stale: bool = False
    message: str | None = None


class OptionChain(BaseModel):
    symbol: str
    underlying_price: float | None = None
    expiry: date | None = None
    atm_strike: float | None = None
    distance_from_spot: float | None = None
    strikes: list[OptionStrike] = []
    source: str
    timestamp: datetime
    status: Status
    is_stale: bool = False
    message: str | None = None
