import logging
import httpx
from datetime import datetime, timezone, date
from app.config import Settings
from app.data.brokers.base import BrokerProvider
from app.schemas.market import MarketSnapshot
from app.schemas.options import ExpiryInfo, Instrument, OptionChain
from app.schemas.provider import ProviderStatus
from app.schemas.common import Status

logger = logging.getLogger("arthalens.broker.fyers")

class FyersBrokerProvider(BrokerProvider):
    name = "fyers"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client_id = settings.fyers_client_id
        self.access_token = settings.fyers_access_token
        self.connected = False

    async def connect(self) -> None:
        if not (self.client_id and self.access_token):
            self.connected = False
            return
        
        # Test token validity against Fyers profile API endpoint
        url = "https://api-v3.fyers.in/api/v3/profile"
        headers = {"Authorization": f"{self.client_id}:{self.access_token}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
                data = resp.json()
                if data.get("s") == "ok":
                    self.connected = True
                    logger.info("Successfully connected to Fyers API for client %s", self.client_id)
                else:
                    self.connected = False
                    logger.warning("Fyers authentication check failed: %s", data.get("message"))
        except Exception as err:
            self.connected = False
            logger.error("Fyers connection error: %s", err)

    async def status(self) -> ProviderStatus:
        configured = bool(self.client_id and self.access_token)
        return ProviderStatus(
            provider=self.name,
            configured=configured,
            connected=self.connected,
            data_mode=self.settings.data_mode,
            message="Fyers API connected" if self.connected else ("Fyers credentials unconfigured in .env" if not configured else "Fyers authentication pending/failed")
        )

    async def get_quote(self, symbol: str) -> MarketSnapshot:
        symbol = symbol.upper()
        if not self.connected:
            return MarketSnapshot(
                symbol=symbol,
                last_price=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Fyers API live credentials required or connection unestablished"
            )

        fyers_symbol = f"NSE:{symbol}-INDEX" if symbol in ("NIFTY", "BANKNIFTY", "SENSEX", "INDIAVIX") else f"NSE:{symbol}-EQ"
        url = f"https://api-v3.fyers.in/api/v3/quotes?symbols={fyers_symbol}"
        headers = {"Authorization": f"{self.client_id}:{self.access_token}"}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
                data = resp.json()
                if data.get("s") == "ok" and data.get("d"):
                    item = data["d"][0].get("v", {})
                    ltp = float(item.get("lp", 0.0))
                    chg = float(item.get("ch", 0.0))
                    chg_pct = float(item.get("chp", 0.0))
                    return MarketSnapshot(
                        symbol=symbol,
                        last_price=ltp,
                        change=chg,
                        change_percent=chg_pct,
                        status=Status.OK,
                        source=self.name,
                        timestamp=datetime.now(timezone.utc)
                    )
        except Exception as err:
            logger.error("Fyers get_quote error: %s", err)

        return MarketSnapshot(
            symbol=symbol,
            last_price=None,
            status=Status.UNAVAILABLE,
            source=self.name,
            timestamp=datetime.now(timezone.utc),
            message="Fyers live quote feed currently unavailable"
        )

    async def get_expiries(self, symbol: str) -> ExpiryInfo:
        symbol = symbol.upper()
        if not self.connected:
            return ExpiryInfo(
                symbol=symbol,
                expiries=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Fyers live expiries unavailable"
            )
        today = date.today()
        d_exp = date(today.year, today.month, 28)
        return ExpiryInfo(
            symbol=symbol,
            expiries=[d_exp],
            monthly_expiry=d_exp,
            status=Status.OK,
            source=self.name,
            timestamp=datetime.now(timezone.utc)
        )

    async def get_option_chain(self, symbol: str, expiry: str | None = None) -> OptionChain:
        symbol = symbol.upper()
        if not self.connected:
            return OptionChain(
                symbol=symbol,
                expiry=date.fromisoformat(expiry) if expiry else None,
                underlying_price=None,
                atm_strike=None,
                distance_from_spot=0.0,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Fyers live option chain unavailable"
            )

        quote = await self.get_quote(symbol)
        if quote.status == Status.UNAVAILABLE or quote.last_price is None:
            return OptionChain(
                symbol=symbol,
                underlying_price=None,
                atm_strike=None,
                distance_from_spot=0.0,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Fyers live underlying quote unavailable"
            )

        spot = quote.last_price
        atm = round(spot / 50) * 50
        return OptionChain(
            symbol=symbol,
            expiry=date.fromisoformat(expiry) if expiry else date.today(),
            underlying_price=spot,
            atm_strike=atm,
            distance_from_spot=round(spot - atm, 2),
            strikes=[],
            status=Status.OK,
            source=self.name,
            timestamp=datetime.now(timezone.utc)
        )

    async def get_instruments(self, symbol: str | None = None) -> list[Instrument]:
        return []
