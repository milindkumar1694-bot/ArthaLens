import asyncio
import logging
import binascii
from datetime import date, datetime, timezone
import re
from collections import defaultdict

import httpx
import pyotp

from app.config import Settings
from app.data.brokers.base import BrokerProvider
from app.data.normalizers.options import normalize_option_chain
from app.schemas.common import Status
from app.schemas.market import MarketSnapshot
from app.schemas.options import ExpiryInfo, Instrument, OptionChain
from app.schemas.provider import ProviderStatus

logger = logging.getLogger("arthalens.broker.angelone")


class AngelOneBrokerProvider(BrokerProvider):
    name = "angelone"

    _AUTH_URL = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
    _LTP_URL = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getLtpData"

    _INDEX_ALIASES = {
        "NIFTY": {"NIFTY", "NIFTY50", "NIFTY 50"},
        "BANKNIFTY": {"BANKNIFTY", "NIFTYBANK", "NIFTY BANK"},
        "SENSEX": {"SENSEX"},
        "INDIAVIX": {"INDIAVIX", "INDIA VIX", "VIX"},
    }

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.angel_one_api_key.strip()
        self.client_id = settings.angel_one_client_id.strip()
        self.password = settings.angel_one_password.strip()
        self.totp = settings.angel_one_totp.strip()
        self.instrument_master_url = settings.angel_one_instrument_master_url

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
                    logger.warning("Angel One authentication failed: %s", data.get("message"))
        except Exception as err:
            self.connected = False
            logger.error("Angel One connection exception: %s", err)

    async def status(self) -> ProviderStatus:
        configured = bool(self.api_key and self.client_id)
        return ProviderStatus(
            provider=self.name,
            configured=self._configuration_complete,
            connected=self.connected,
            status="ok" if self.connected else "unavailable",
            message="Angel One SmartAPI connected" if self.connected else ("Angel One credentials unconfigured in .env" if not configured else "Angel One authentication pending/failed")
        )

    async def get_quote(self, symbol: str) -> MarketSnapshot:
        symbol = symbol.upper()
        if not self.connected:
            await self.ensure_connected()

        if not self.connected:
            return MarketSnapshot(
                symbol=symbol,
                last_price=None,
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

        exchange = str(instrument.get("exch_seg") or "NSE").upper()
        trading_symbol = str(instrument.get("symbol") or instrument.get("tradingsymbol") or "").strip()
        token = str(instrument.get("token") or "").strip()
        if not trading_symbol or not token:
            return MarketSnapshot(
                symbol=symbol,
                last_price=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=f"Angel One token mapping incomplete for {symbol}",
            )

        quote_data = await self._ltp(exchange, trading_symbol, token)
        if not quote_data:
            return MarketSnapshot(
                symbol=symbol,
                exchange=exchange,
                last_price=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One live quote feed currently unavailable",
            )

        ltp = float(quote_data.get("ltp") or 0.0)
        close = float(quote_data.get("close") or 0.0) or None
        open_price = float(quote_data.get("open") or 0.0) or None
        high = float(quote_data.get("high") or 0.0) or None
        low = float(quote_data.get("low") or 0.0) or None
        change = round(ltp - close, 2) if close is not None else None
        change_percent = round(change / close * 100.0, 3) if close not in (None, 0) and change is not None else None

        return MarketSnapshot(
            symbol=symbol,
            exchange=exchange,
            last_price=ltp,
            change=change,
            change_percent=change_percent,
            open=open_price,
            high=high,
            low=low,
            previous_close=close,
            timestamp=datetime.now(timezone.utc),
            source=self.name,
            status=Status.OK,
            market_status="OPEN" if ltp > 0 else "UNKNOWN",
        )

    async def get_instruments(self, symbol: str | None = None) -> list[Instrument]:
        target = symbol.upper() if symbol else None
        loaded = await self._load_instrument_master()
        if not loaded:
            return []

        instruments: list[Instrument] = []
        for row in self._instrument_master_rows:
            candidate = self._to_option_instrument(row, target) if target else None
            if target:
                if candidate:
                    instruments.append(candidate)
                continue
            for underlying in ("NIFTY", "BANKNIFTY"):
                candidate = self._to_option_instrument(row, underlying)
                if candidate:
                    instruments.append(candidate)
                    break
        instruments.sort(key=lambda item: (item.expiry or date.max, item.strike or 0.0, item.option_type or ""))
        return instruments

    async def get_expiries(self, symbol: str) -> ExpiryInfo:
        symbol = symbol.upper()
        if not self.connected:
            return ExpiryInfo(
                symbol=symbol,
                expiries=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One expiry metadata unavailable",
            )

        # Dynamic expiry calculation
        today = date.today()
        d_exp = date(today.year, today.month, 28)
        return ExpiryInfo(
            symbol=symbol,
            expiries=expiries,
            nearest_expiry=nearest,
            next_expiry=next_expiry,
            monthly_expiry=monthly,
            status=Status.OK,
            source=self.name,
            timestamp=datetime.now(timezone.utc),
        )

    async def get_option_chain(self, symbol: str, expiry: str | None = None) -> OptionChain:
        symbol = symbol.upper()
        if not self.connected:
            await self.ensure_connected()

        if not self.connected:
            return OptionChain(
                symbol=symbol,
                expiry=self._parse_expiry(expiry),
                underlying_price=None,
                atm_strike=None,
                distance_from_spot=None,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One live option chain unavailable: authentication failed or not connected",
            )

        quote = await self.get_quote(symbol)
        if quote.status != Status.OK or quote.last_price is None:
            return OptionChain(
                symbol=symbol,
                expiry=self._parse_expiry(expiry),
                underlying_price=None,
                atm_strike=None,
                distance_from_spot=None,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One live underlying quote unavailable",
            )

        instruments = await self.get_instruments(symbol)
        if not instruments:
            return OptionChain(
                symbol=symbol,
                expiry=self._parse_expiry(expiry),
                underlying_price=quote.last_price,
                atm_strike=None,
                distance_from_spot=None,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One option instruments unavailable",
            )

        available_expiries = sorted({item.expiry for item in instruments if item.expiry})
        selected_expiry = self._parse_expiry(expiry) if expiry else available_expiries[0]
        if not selected_expiry:
            return OptionChain(
                symbol=symbol,
                expiry=None,
                underlying_price=quote.last_price,
                atm_strike=None,
                distance_from_spot=None,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One expiry selection unavailable",
            )

        selected = [item for item in instruments if item.expiry == selected_expiry]
        if not selected:
            return OptionChain(
                symbol=symbol,
                expiry=selected_expiry,
                underlying_price=quote.last_price,
                atm_strike=None,
                distance_from_spot=None,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=f"Angel One option instruments unavailable for expiry {selected_expiry.isoformat()}",
            )

        strikes = sorted({item.strike for item in selected if item.strike is not None})
        if not strikes:
            return OptionChain(
                symbol=symbol,
                expiry=selected_expiry,
                underlying_price=quote.last_price,
                atm_strike=None,
                distance_from_spot=None,
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
            expiry=selected_expiry,
            source=self.name,
            underlying_price=quote.last_price,
        )

    async def get_instruments(self, symbol: str | None = None) -> list[Instrument]:
        return []
