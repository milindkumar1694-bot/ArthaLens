from datetime import date, datetime, timezone
from collections.abc import Iterable, Mapping
from app.schemas.common import Status
from app.schemas.options import OptionChain, OptionLeg, OptionStrike


def normalize_option_chain(raw_contracts: Iterable[Mapping[str, object]], *, symbol: str, expiry: date, source: str, underlying_price: float | None) -> OptionChain:
    """Validate and combine contract records into strike-centric CE/PE rows without inventing missing fields."""
    rows: dict[float, dict[str, OptionLeg]] = {}
    invalid = 0
    for raw in raw_contracts:
        try:
            strike, option_type = float(raw["strike"]), str(raw["option_type"]).upper()
            if strike <= 0 or option_type not in {"CE", "PE"}: raise ValueError
            if strike not in rows: rows[strike] = {}
            if option_type in rows[strike]: raise ValueError("duplicate contract")
            def n(name: str, integer: bool = False):
                value = raw.get(name)
                return (int(value) if integer else float(value)) if value is not None else None
            oi, volume = n("oi", True), n("volume", True)
            if (oi is not None and oi < 0) or (volume is not None and volume < 0): raise ValueError
            rows[strike][option_type] = OptionLeg(symbol=str(raw.get("symbol")) if raw.get("symbol") else None, oi=oi,
                change_oi=n("change_oi", True), volume=volume, iv=n("iv"), ltp=n("ltp"), bid=n("bid"), ask=n("ask"))
        except (KeyError, TypeError, ValueError): invalid += 1
    strikes = [OptionStrike(strike=strike, ce=legs.get("CE"), pe=legs.get("PE")) for strike, legs in sorted(rows.items())]
    atm = min((item.strike for item in strikes), key=lambda item: abs(item-underlying_price), default=None) if underlying_price is not None else None
    return OptionChain(symbol=symbol.upper(), underlying_price=underlying_price, expiry=expiry, atm_strike=atm,
        distance_from_spot=abs(atm-underlying_price) if atm is not None and underlying_price is not None else None, strikes=strikes,
        source=source, timestamp=datetime.now(timezone.utc), status=Status.PARTIAL if invalid else Status.OK,
        message=f"{invalid} malformed or duplicate contracts excluded" if invalid else None)
