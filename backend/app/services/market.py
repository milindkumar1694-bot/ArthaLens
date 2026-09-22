from datetime import datetime, timezone
from app.config import Settings
from app.data.brokers import BrokerProvider, MockBrokerProvider
from app.schemas.common import Status
from app.schemas.market import MarketSnapshot
from app.schemas.provider import ProviderStatus
from app.schemas.options import ExpiryInfo, OptionChain
from .cache import Cache


SUPPORTED_SYMBOLS = {"NIFTY", "BANKNIFTY", "SENSEX", "INDIAVIX"}


class MarketDataService:
    def __init__(self, settings: Settings, cache: Cache | None = None): self.settings = settings; self.cache = cache or Cache(); self._provider = self._select_provider()
    def _select_provider(self) -> BrokerProvider | None:
        if self.settings.data_mode == "mock" and self.settings.provider_name in {"", "mock"}:
            return MockBrokerProvider()
        if self.settings.data_mode == "live":
            p = self.settings.provider_name
            if p in ("angelone", "smartapi"):
                from app.data.brokers.angel_one import AngelOneBrokerProvider
                return AngelOneBrokerProvider(self.settings)
            if p == "fyers":
                from app.data.brokers.fyers import FyersBrokerProvider
                return FyersBrokerProvider(self.settings)
        return None
    def _stale(self, value: MarketSnapshot | OptionChain, maximum_age: int):
        age = (datetime.now(timezone.utc) - value.timestamp).total_seconds()
        if age > maximum_age: return value.model_copy(update={"is_stale": True, "status": Status.STALE, "message": "Data exceeded configured freshness threshold."})
        return value
    async def quote(self, symbol: str) -> MarketSnapshot:
        symbol = symbol.upper()
        if symbol not in SUPPORTED_SYMBOLS: raise ValueError(f"Unsupported market symbol: {symbol}")
        key = f"market:{symbol}"; cached = await self.cache.get(key, MarketSnapshot)
        if cached: return self._stale(cached, self.settings.max_market_data_age_seconds)
        if self._provider:
            result = await self._provider.get_quote(symbol); await self.cache.set(key, result, self.settings.market_cache_ttl_seconds); return self._stale(result, self.settings.max_market_data_age_seconds)
        return MarketSnapshot(symbol=symbol, timestamp=datetime.now(timezone.utc), source="not_configured",
            status=Status.UNAVAILABLE, message="Market data provider is not configured. Live mode never falls back to mock data.")
    async def provider_status(self) -> ProviderStatus:
        if self._provider: return await self._provider.status()
        return ProviderStatus(provider=self.settings.provider_name or "none", configured=False, connected=False,
            status=Status.UNAVAILABLE, message="Broker provider not configured")
    async def expiries(self, symbol: str) -> ExpiryInfo:
        if symbol.upper() not in {"NIFTY", "BANKNIFTY"}: raise ValueError(f"Unsupported option underlying: {symbol}")
        key = f"expiries:{symbol.upper()}"; cached = await self.cache.get(key, ExpiryInfo)
        if cached: return cached
        if self._provider:
            result = await self._provider.get_expiries(symbol); await self.cache.set(key, result, self.settings.expiry_cache_ttl_seconds); return result
        return ExpiryInfo(symbol=symbol.upper(), expiries=[], source="not_configured", timestamp=datetime.now(timezone.utc), status=Status.UNAVAILABLE, message="Market data provider is not configured.")
    async def option_chain(self, symbol: str, expiry: str | None = None, strike_range: int | None = None) -> OptionChain:
        symbol = symbol.upper()
        if symbol not in {"NIFTY", "BANKNIFTY"}: raise ValueError(f"Unsupported option underlying: {symbol}")
        key = f"chain:{symbol}:{expiry or 'nearest'}"; cached = await self.cache.get(key, OptionChain)
        if cached: result = cached
        elif self._provider:
            result = await self._provider.get_option_chain(symbol, expiry); await self.cache.set(key, result, self.settings.option_chain_cache_ttl_seconds)
        else: return OptionChain(symbol=symbol, source="not_configured", timestamp=datetime.now(timezone.utc), status=Status.UNAVAILABLE, message="Option-chain data unavailable: broker provider is not configured.")
        result = self._stale(result, self.settings.max_option_chain_age_seconds)
        if strike_range is not None and result.atm_strike is not None: result = result.model_copy(update={"strikes": [x for x in result.strikes if abs(x.strike-result.atm_strike) <= strike_range]})
        return result
