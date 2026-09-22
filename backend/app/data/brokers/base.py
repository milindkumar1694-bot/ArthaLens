from abc import ABC, abstractmethod
from app.schemas.market import MarketSnapshot
from app.schemas.provider import ProviderStatus
from app.schemas.options import ExpiryInfo, Instrument, OptionChain


class BrokerProvider(ABC):
    """Broker-neutral extension point. Live adapters must normalize no data themselves."""
    name: str
    @abstractmethod
    async def get_quote(self, symbol: str) -> MarketSnapshot: ...
    @abstractmethod
    async def status(self) -> ProviderStatus: ...
    async def get_historical_candles(self, symbol: str): raise NotImplementedError
    async def get_option_chain(self, symbol: str, expiry: str | None = None) -> OptionChain: raise NotImplementedError
    async def get_expiries(self, symbol: str) -> ExpiryInfo: raise NotImplementedError
    async def get_instruments(self, symbol: str | None = None) -> list[Instrument]: raise NotImplementedError
    async def get_futures(self, symbol: str): raise NotImplementedError
    async def connect(self) -> None: raise NotImplementedError
    async def disconnect(self) -> None: return None
