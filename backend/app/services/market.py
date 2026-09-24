from datetime import datetime, timezone
import logging

from app.config import Settings
from app.data.brokers import BrokerProvider, MockBrokerProvider
from app.schemas.common import Status
from app.schemas.market import MarketSnapshot
from app.schemas.options import ExpiryInfo, OptionChain
from app.schemas.provider import ProviderStatus
from .cache import Cache

logger = logging.getLogger("arthalens.market")


SUPPORTED_SYMBOLS = {
    "NIFTY",
    "BANKNIFTY",
    "SENSEX",
    "INDIAVIX",
}


class MarketDataService:
    def __init__(
        self,
        settings: Settings,
        cache: Cache | None = None,
    ):
        self.settings = settings
        self.cache = cache or Cache()
        self._provider = self._select_provider()

    @property
    def provider(self) -> BrokerProvider | None:
        return self._provider

    async def connect(self) -> ProviderStatus:
        """
        Connect the single provider instance used by the whole app.
        """
        if not self._provider:
            return await self.provider_status()

        try:
            await self._provider.connect()
        except Exception as exc:
            logger.exception(
                "Provider connect failed provider=%s error=%s",
                self._provider.name,
                exc,
            )

        return await self._provider.status()

    async def disconnect(self) -> None:
        if not self._provider:
            return

        try:
            await self._provider.disconnect()
        except Exception as exc:
            logger.warning(
                "Provider disconnect failed provider=%s error=%s",
                self._provider.name,
                exc,
            )

    def _select_provider(
        self,
    ) -> BrokerProvider | None:
        if (
            self.settings.data_mode == "mock"
            and self.settings.provider_name in {"", "mock"}
        ):
            return MockBrokerProvider()

        if self.settings.data_mode == "live":
            provider_name = self.settings.provider_name

            if provider_name in {
                "angelone",
                "smartapi",
            }:
                from app.data.brokers.angel_one import (
                    AngelOneBrokerProvider,
                )

                return AngelOneBrokerProvider(
                    self.settings
                )

            if provider_name == "fyers":
                from app.data.brokers.fyers import (
                    FyersBrokerProvider,
                )

                return FyersBrokerProvider(
                    self.settings
                )

        return None

    def _stale(
        self,
        value: MarketSnapshot | OptionChain,
        maximum_age: int,
    ):
        age = (
            datetime.now(timezone.utc)
            - value.timestamp
        ).total_seconds()

        if age > maximum_age:
            return value.model_copy(
                update={
                    "is_stale": True,
                    "status": Status.STALE,
                    "message": (
                        "Data exceeded configured "
                        "freshness threshold."
                    ),
                }
            )

        return value

    async def quote(
        self,
        symbol: str,
    ) -> MarketSnapshot:
        symbol = symbol.upper()

        if symbol not in SUPPORTED_SYMBOLS:
            raise ValueError(
                f"Unsupported market symbol: {symbol}"
            )

        key = f"market:{symbol}"

        cached = await self.cache.get(
            key,
            MarketSnapshot,
        )

        if cached:
            return self._stale(
                cached,
                self.settings.max_market_data_age_seconds,
            )

        if not self._provider:
            return MarketSnapshot(
                symbol=symbol,
                timestamp=datetime.now(timezone.utc),
                source="not_configured",
                status=Status.UNAVAILABLE,
                message=(
                    "Market data provider is not configured. "
                    "Live mode never falls back to mock data."
                ),
            )

        try:
            result = await self._provider.get_quote(
                symbol
            )
        except Exception as exc:
            logger.exception(
                "Market quote failed symbol=%s error=%s",
                symbol,
                exc,
            )

            result = MarketSnapshot(
                symbol=symbol,
                timestamp=datetime.now(timezone.utc),
                source=self._provider.name,
                status=Status.UNAVAILABLE,
                message="Market provider request failed.",
            )

        # Do not cache an unavailable response.
        # This allows the next request/scheduler tick to recover
        # immediately after a transient provider failure.
        if result.status in {
            Status.OK,
            Status.PARTIAL,
            Status.STALE,
        }:
            await self.cache.set(
                key,
                result,
                self.settings.market_cache_ttl_seconds,
            )

        return self._stale(
            result,
            self.settings.max_market_data_age_seconds,
        )

    async def provider_status(
        self,
    ) -> ProviderStatus:
        if self._provider:
            return await self._provider.status()

        return ProviderStatus(
            provider=self.settings.provider_name or "none",
            configured=False,
            connected=False,
            status=Status.UNAVAILABLE,
            message=(
                "Broker provider not configured"
            ),
        )

    async def expiries(
        self,
        symbol: str,
    ) -> ExpiryInfo:
        symbol = symbol.upper()

        if symbol not in {
            "NIFTY",
            "BANKNIFTY",
        }:
            raise ValueError(
                f"Unsupported option underlying: {symbol}"
            )

        key = f"expiries:{symbol}"

        cached = await self.cache.get(
            key,
            ExpiryInfo,
        )

        if cached:
            return cached

        if not self._provider:
            return ExpiryInfo(
                symbol=symbol,
                expiries=[],
                source="not_configured",
                timestamp=datetime.now(timezone.utc),
                status=Status.UNAVAILABLE,
                message=(
                    "Market data provider is not configured."
                ),
            )

        result = await self._provider.get_expiries(
            symbol
        )

        if result.status in {
            Status.OK,
            Status.PARTIAL,
        }:
            await self.cache.set(
                key,
                result,
                self.settings.expiry_cache_ttl_seconds,
            )

        return result

    async def option_chain(
        self,
        symbol: str,
        expiry: str | None = None,
        strike_range: int | None = None,
    ) -> OptionChain:
        symbol = symbol.upper()

        if symbol not in {
            "NIFTY",
            "BANKNIFTY",
        }:
            raise ValueError(
                f"Unsupported option underlying: {symbol}"
            )

        key = (
            f"chain:{symbol}:"
            f"{expiry or 'nearest'}"
        )

        cached = await self.cache.get(
            key,
            OptionChain,
        )

        if cached:
            result = cached
        elif self._provider:
            result = await self._provider.get_option_chain(
                symbol,
                expiry,
            )

            if result.status in {
                Status.OK,
                Status.PARTIAL,
            }:
                await self.cache.set(
                    key,
                    result,
                    self.settings.option_chain_cache_ttl_seconds,
                )
        else:
            return OptionChain(
                symbol=symbol,
                source="not_configured",
                timestamp=datetime.now(timezone.utc),
                status=Status.UNAVAILABLE,
                message=(
                    "Option-chain data unavailable: "
                    "broker provider is not configured."
                ),
            )

        result = self._stale(
            result,
            self.settings.max_option_chain_age_seconds,
        )

        if (
            strike_range is not None
            and result.atm_strike is not None
        ):
            result = result.model_copy(
                update={
                    "strikes": [
                        strike
                        for strike in result.strikes
                        if abs(
                            strike.strike
                            - result.atm_strike
                        ) <= strike_range
                    ]
                }
            )

        return result
