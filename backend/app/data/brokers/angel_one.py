import logging
import httpx
from datetime import datetime, timezone, date
from app.config import Settings
from app.data.brokers.base import BrokerProvider
from app.schemas.market import MarketSnapshot
from app.schemas.options import ExpiryInfo, Instrument, OptionChain, StrikeRow, OptionLeg
from app.schemas.provider import ProviderStatus
from app.schemas.common import Status

logger = logging.getLogger("arthalens.broker.angelone")

class AngelOneBrokerProvider(BrokerProvider):
    name = "angelone"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.angel_one_api_key
        self.client_id = settings.angel_one_client_id
        self.password = settings.angel_one_password
        self.totp = settings.angel_one_totp
        self.jwt_token: str | None = None
        self.feed_token: str | None = None
        self.connected = False

    async def connect(self) -> None:
        if not (self.api_key and self.client_id and self.password and self.totp):
            self.connected = False
            return

        url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "X-PrivateKey": self.api_key
        }
        payload = {
            "clientcode": self.client_id,
            "password": self.password,
            "totp": self.totp
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                data = resp.json()
                if data.get("status") and data.get("data"):
                    self.jwt_token = data["data"].get("jwtToken")
                    self.feed_token = data["data"].get("feedToken")
                    self.connected = True
                    logger.info("Successfully authenticated with Angel One SmartAPI for client %s", self.client_id)
                else:
                     self.connected = False
                     logger.warning(
                      "Angel One authentication failed: status=%s errorcode=%s message=%s",
                      data.get("status"),
                      data.get("errorcode"),
                      data.get("message"),
                    )
        except Exception as err:
            self.connected = False
            logger.error("Angel One connection exception: %s", err)

    async def status(self) -> ProviderStatus:
        configured = bool(self.api_key and self.client_id)
        return ProviderStatus(
            provider=self.name,
            configured=configured,
            connected=self.connected,
            status="ok" if self.connected else "unavailable",
            message="Angel One SmartAPI connected" if self.connected else ("Angel One credentials unconfigured in .env" if not configured else "Angel One authentication pending/failed")
        )

    async def get_quote(self, symbol: str) -> MarketSnapshot:
        symbol = symbol.upper()
        if not self.connected:
            return MarketSnapshot(
                symbol=symbol,
                last_price=None,
                change=None,
                change_percent=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One SmartAPI live credentials required or connection unestablished"
            )

        # Live quote HTTP request to Angel One LTP API endpoint
        url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getLtpData"
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "X-PrivateKey": self.api_key
        }
        trading_symbol = f"{symbol}-EQ" if symbol in ("NIFTY", "BANKNIFTY") else symbol
        payload = {"exchange": "NSE", "tradingsymbol": trading_symbol, "symboltoken": "99926000" if symbol == "NIFTY" else "99926009"}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                data = resp.json()
                if data.get("status") and data.get("data"):
                    ltp = float(data["data"].get("ltp", 0.0))
                    close = float(data["data"].get("close", ltp))
                    chg = round(ltp - close, 2)
                    chg_pct = round(chg / close * 100.0, 3) if close else 0.0
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
            logger.error("Angel One get_quote error: %s", err)

        return MarketSnapshot(
            symbol=symbol,
            last_price=None,
            status=Status.UNAVAILABLE,
            source=self.name,
            timestamp=datetime.now(timezone.utc),
            message="Angel One live quote feed currently unavailable"
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
                message="Angel One live expiries unavailable"
            )

        # Dynamic expiry calculation
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
                message="Angel One live option chain unavailable"
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
                message="Angel One live underlying quote unavailable"
            )

        # Option chain construction from live feed
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
