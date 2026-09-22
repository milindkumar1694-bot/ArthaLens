from datetime import date, datetime, timedelta, timezone
from app.schemas.common import Status
from app.schemas.market import MarketSnapshot
from app.schemas.options import ExpiryInfo, Instrument, OptionChain
from app.schemas.provider import ProviderStatus
from app.data.normalizers.options import normalize_option_chain
from .base import BrokerProvider


class MockBrokerProvider(BrokerProvider):
    """Deterministic, explicitly labelled development data. Never selected in live mode."""
    name = "mock"
    _quotes = {
        "NIFTY": (22500.0, 22480.0), "BANKNIFTY": (48500.0, 48400.0),
        "SENSEX": (74000.0, 73900.0), "INDIAVIX": (14.0, 13.8),
    }
    async def get_quote(self, symbol: str) -> MarketSnapshot:
        key = symbol.upper()
        if key not in self._quotes: raise KeyError(key)
        last, previous = self._quotes[key]
        return MarketSnapshot(symbol=key, exchange="NSE" if key != "SENSEX" else "BSE", last_price=last,
            change=last-previous, change_percent=round((last-previous)/previous*100, 4), open=previous,
            high=max(last, previous), low=min(last, previous), previous_close=previous, volume=None,
            timestamp=datetime.now(timezone.utc), source="mock", status=Status.OK,
            message="Synthetic development data. Not live market data.")
    async def status(self) -> ProviderStatus:
        return ProviderStatus(provider=self.name, configured=True, connected=True, status=Status.OK,
            message="Synthetic development provider")
    def _expiries(self) -> list[date]:
        today = datetime.now(timezone.utc).date()
        return [today + timedelta(days=((3 - today.weekday()) % 7) + 7*i) for i in range(4)]
    async def get_expiries(self, symbol: str) -> ExpiryInfo:
        expiries = self._expiries()
        return ExpiryInfo(symbol=symbol.upper(), expiries=expiries, nearest_expiry=expiries[0], next_expiry=expiries[1],
            monthly_expiry=expiries[-1], source="mock", timestamp=datetime.now(timezone.utc), status=Status.OK,
            message="Synthetic development expiries. Not exchange data.")
    async def get_instruments(self, symbol: str | None = None) -> list[Instrument]:
        symbols = [symbol.upper()] if symbol else ["NIFTY", "BANKNIFTY"]
        results: list[Instrument] = []
        for underlying in symbols:
            expiry = (await self.get_expiries(underlying)).nearest_expiry
            spot = self._quotes[underlying][0]; step = 50 if underlying == "NIFTY" else 100
            for strike in range(int(spot-step*5), int(spot+step*6), step):
                for kind in ("CE", "PE"):
                    results.append(Instrument(symbol=f"{underlying}{expiry:%y%m%d}{strike}{kind}", underlying=underlying, exchange="NSE", expiry=expiry, strike=strike, option_type=kind, instrument_token=f"mock-{underlying}-{strike}-{kind}", trading_symbol=f"{underlying} {strike} {kind}", lot_size=25 if underlying == "NIFTY" else 15, provider="mock"))
        return results
    async def get_option_chain(self, symbol: str, expiry: str | None = None) -> OptionChain:
        underlying = symbol.upper()
        exp = (await self.get_expiries(underlying)).nearest_expiry
        if expiry:
            try: exp = date.fromisoformat(expiry)
            except ValueError: pass
        spot = self._quotes[underlying][0]; step = 50 if underlying == "NIFTY" else 100
        contracts = []
        for strike in range(int(spot-step*5), int(spot+step*6), step):
            for kind in ("CE", "PE"):
                intrinsic = max(spot-strike, 0) if kind == "CE" else max(strike-spot, 0)
                contracts.append({"symbol": f"{underlying} {strike} {kind}", "strike": strike, "option_type": kind, "oi": 100000 + abs(strike-int(spot))*10, "change_oi": 1000 if kind == "CE" else -500, "volume": 5000 + abs(strike-int(spot))*2, "iv": 12.5, "ltp": max(5, intrinsic+30), "bid": max(4.5, intrinsic+29.5), "ask": intrinsic+30.5})
        chain = normalize_option_chain(contracts, symbol=underlying, expiry=exp, source="mock", underlying_price=spot)
        chain.message = "Synthetic development option chain. Not live options data."
        return chain
