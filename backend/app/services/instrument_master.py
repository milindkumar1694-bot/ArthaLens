import logging
from datetime import date
from pydantic import BaseModel
from app.schemas.options import Instrument

logger = logging.getLogger("arthalens.instruments")

class InstrumentMasterService:
    def __init__(self):
        self._cache: dict[str, Instrument] = {}

    def discover_strike_instrument(
        self,
        symbol: str,
        expiry: date,
        strike: float,
        option_type: str,
        exchange: str = "NFO"
    ) -> Instrument:
        trading_symbol = f"{symbol.upper()}{expiry:%y%b%d}{int(strike)}{option_type.upper()}"
        token = f"TOKEN-{symbol.upper()}-{int(strike)}-{option_type.upper()}"
        lot_size = 15 if "BANK" in symbol.upper() else (25 if "FIN" in symbol.upper() else 50)
        
        inst = Instrument(
            symbol=trading_symbol,
            underlying=symbol.upper(),
            exchange=exchange,
            expiry=expiry,
            strike=strike,
            option_type=option_type.upper(),
            instrument_token=token,
            trading_symbol=trading_symbol,
            lot_size=lot_size,
            provider="master"
        )
        self._cache[trading_symbol] = inst
        return inst

    def get_cached_instrument(self, trading_symbol: str) -> Instrument | None:
        return self._cache.get(trading_symbol)
