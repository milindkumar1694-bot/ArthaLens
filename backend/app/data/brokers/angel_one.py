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
        self.authentication_attempted = False
        self.last_auth_reason: str | None = None
        self.last_auth_http_status: int | None = None
        self.last_success_at: datetime | None = None

        self._http_client: httpx.AsyncClient | None = None
        self._instrument_master_rows: list[dict] = []
        self._instrument_master_loaded_at: datetime | None = None

    @property
    def _configuration_complete(self) -> bool:
        return bool(self.api_key and self.client_id and self.password and self.totp)

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "X-PrivateKey": self.api_key,
        }

    async def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=15.0)
        return self._http_client

    def _clear_auth(self, reason: str | None = None) -> None:
        self.connected = False
        self.jwt_token = None
        self.feed_token = None
        self.last_auth_reason = reason

    def _auth_diagnostics(self) -> dict[str, bool]:
        return {
            "angelone_auth_attempt": True,
            "client_id_present": bool(self.client_id),
            "api_key_present": bool(self.api_key),
            "password_present": bool(self.password),
            "totp_present": bool(self.totp),
        }

    def _generate_totp(self) -> str | None:
        if not self.totp:
            return None
        normalized_secret = self.totp.replace(" ", "").upper()
        try:
            code = pyotp.TOTP(normalized_secret).now()
        except (binascii.Error, TypeError, ValueError):
            return None
        return code

    async def connect(self) -> None:
        self.authentication_attempted = True
        diagnostics = self._auth_diagnostics()
        logger.info(
            "Angel One authentication attempt angelone_auth_attempt=%s client_id_present=%s api_key_present=%s password_present=%s totp_present=%s",
            diagnostics["angelone_auth_attempt"],
            diagnostics["client_id_present"],
            diagnostics["api_key_present"],
            diagnostics["password_present"],
            diagnostics["totp_present"],
        )
        if not self._configuration_complete:
            self._clear_auth("missing_credentials")
            logger.warning("Angel One authentication skipped: missing required credentials api_key/client_id/password/totp")
            return

        totp_code = self._generate_totp()
        if not totp_code:
            self._clear_auth("invalid_totp_configuration")
            logger.warning(
                "Angel One authentication skipped: invalid totp configuration (expected ANGEL_ONE_TOTP as TOTP secret)"
            )
            return

        payload = {
            "clientcode": self.client_id,
            "password": self.password,
            "totp": totp_code,
        }

        try:
            client = await self._client()
            resp = await client.post(self._AUTH_URL, json=payload, headers=self._auth_headers())
            self.last_auth_http_status = resp.status_code
            data = resp.json() if resp.content else {}
            response_status = data.get("status")
            response_errorcode = data.get("errorcode")
            response_message = data.get("message")
            auth_data = data.get("data") if isinstance(data, dict) else None

            jwt_token = auth_data.get("jwtToken") if isinstance(auth_data, dict) else None
            feed_token = auth_data.get("feedToken") if isinstance(auth_data, dict) else None
            if resp.status_code == 200 and response_status is True and jwt_token and feed_token:
                self.jwt_token = jwt_token
                self.feed_token = feed_token
                self.connected = True
                self.last_auth_reason = "success"
                self.last_success_at = datetime.now(timezone.utc)
                logger.info("Angel One authentication successful provider_connected=%s", self.connected)
                return

            self._clear_auth("authentication_failed")
            logger.warning(
                "Angel One authentication failed http_status=%s response_status=%s errorcode=%s message=%s provider_connected=%s",
                resp.status_code,
                response_status,
                response_errorcode,
                response_message,
                self.connected,
            )
        except httpx.HTTPError as err:
            self._clear_auth("network_failure")
            logger.error("Angel One authentication HTTP error provider_connected=%s error=%s", self.connected, err)
        except Exception as err:
            self._clear_auth("unexpected_error")
            logger.error("Angel One authentication unexpected error provider_connected=%s error=%s", self.connected, err)

    async def disconnect(self) -> None:
        self._clear_auth("disconnected")
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def _parse_expiry(self, raw: object) -> date | None:
        if raw in (None, ""):
            return None
        text = str(raw).strip()
        for fmt in ("%d%b%Y", "%d%b%y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_strike(self, raw: object) -> float | None:
        if raw in (None, ""):
            return None
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        if value <= 0:
            return None
        if value > 100000:
            value = value / 100
        return value

    async def _load_instrument_master(self, force_refresh: bool = False) -> bool:
        if not force_refresh and self._instrument_master_rows and self._instrument_master_loaded_at:
            age = (datetime.now(timezone.utc) - self._instrument_master_loaded_at).total_seconds()
            if age < self.settings.instrument_master_cache_seconds:
                return True

        if not self.instrument_master_url:
            logger.warning("Angel One instrument master unavailable: ANGEL_ONE_INSTRUMENT_MASTER_URL missing")
            return False

        try:
            client = await self._client()
            resp = await client.get(self.instrument_master_url)
            if resp.status_code != 200:
                logger.warning("Angel One instrument master load failed http_status=%s", resp.status_code)
                return False
            payload = resp.json()
            if not isinstance(payload, list):
                logger.warning("Angel One instrument master load failed: unexpected payload")
                return False
            self._instrument_master_rows = [item for item in payload if isinstance(item, dict)]
            self._instrument_master_loaded_at = datetime.now(timezone.utc)
            logger.info("Angel One instrument master loaded rows=%s", len(self._instrument_master_rows))
            return True
        except httpx.HTTPError as err:
            logger.error("Angel One instrument master HTTP error: %s", err)
            return False
        except Exception as err:
            logger.error("Angel One instrument master unexpected error: %s", err)
            return False

    def _normalize_symbol_text(self, value: str | None) -> str:
        if not value:
            return ""
        return re.sub(r"[^A-Z0-9]", "", value.upper())

    def _index_instrument(self, symbol: str) -> dict | None:
        aliases = self._INDEX_ALIASES.get(symbol, {symbol})
        alias_tokens = {self._normalize_symbol_text(item) for item in aliases}
        for item in self._instrument_master_rows:
            exch = str(item.get("exch_seg") or "").upper()
            if exch not in {"NSE", "BSE", "NSE_IDX", "BSE_IDX"}:
                continue
            combined = self._normalize_symbol_text(" ".join(str(item.get(k) or "") for k in ("symbol", "name", "tradingsymbol")))
            if any(alias in combined for alias in alias_tokens):
                return item
        return None

    def _to_option_instrument(self, row: dict, symbol: str) -> Instrument | None:
        exch_seg = str(row.get("exch_seg") or "").upper()
        instrument_type = str(row.get("instrumenttype") or row.get("instrument_type") or "").upper()
        if exch_seg != "NFO":
            return None
        if "OPT" not in instrument_type:
            return None

        option_symbol = str(row.get("symbol") or row.get("tradingsymbol") or "").upper()
        name = str(row.get("name") or "").upper()
        if symbol not in {name, option_symbol} and symbol not in option_symbol:
            return None

        option_type = None
        if option_symbol.endswith("CE"):
            option_type = "CE"
        elif option_symbol.endswith("PE"):
            option_type = "PE"
        if option_type is None:
            return None

        expiry = self._parse_expiry(row.get("expiry"))
        strike = self._parse_strike(row.get("strike"))
        token = str(row.get("token") or "").strip()
        trading_symbol = str(row.get("symbol") or row.get("tradingsymbol") or "").strip()

        if not expiry or strike is None or not token or not trading_symbol:
            return None

        lot_size_raw = row.get("lotsize")
        lot_size = int(float(lot_size_raw)) if lot_size_raw not in (None, "") else None

        return Instrument(
            symbol=trading_symbol,
            underlying=symbol,
            exchange=exch_seg,
            expiry=expiry,
            strike=strike,
            option_type=option_type,
            instrument_token=token,
            trading_symbol=trading_symbol,
            lot_size=lot_size,
            provider=self.name,
        )

    async def _ltp(self, exchange: str, trading_symbol: str, token: str) -> dict | None:
        if not self.connected or not self.jwt_token:
            return None

        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-PrivateKey": self.api_key,
        }
        payload = {
            "exchange": exchange,
            "tradingsymbol": trading_symbol,
            "symboltoken": token,
        }
        try:
            client = await self._client()
            resp = await client.post(self._LTP_URL, json=payload, headers=headers)
            data = resp.json() if resp.content else {}
            if resp.status_code == 200 and isinstance(data, dict) and data.get("status") is True and data.get("data"):
                return data["data"]
            logger.warning(
                "Angel One LTP unavailable exchange=%s symbol=%s token=%s http_status=%s status=%s errorcode=%s message=%s",
                exchange,
                trading_symbol,
                token,
                resp.status_code,
                data.get("status") if isinstance(data, dict) else None,
                data.get("errorcode") if isinstance(data, dict) else None,
                data.get("message") if isinstance(data, dict) else None,
            )
            return None
        except httpx.HTTPError as err:
            logger.error("Angel One LTP HTTP error exchange=%s symbol=%s error=%s", exchange, trading_symbol, err)
            return None
        except Exception as err:
            logger.error("Angel One LTP unexpected error exchange=%s symbol=%s error=%s", exchange, trading_symbol, err)
            return None

    async def status(self) -> ProviderStatus:
        if not self._configuration_complete:
            message = "Angel One credentials incomplete: api_key/client_id/password/totp required"
        elif self.connected:
            message = "Angel One SmartAPI authenticated"
        elif self.authentication_attempted:
            message = "Angel One authentication failed or connection unavailable"
        else:
            message = "Angel One authentication not attempted"

        return ProviderStatus(
            provider=self.name,
            configured=self._configuration_complete,
            connected=self.connected,
            status=Status.OK if self.connected else Status.UNAVAILABLE,
            message=message,
            last_success=self.last_success_at,
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
                message="Angel One SmartAPI authentication failed or connection unavailable",
            )

        loaded = await self._load_instrument_master()
        if not loaded:
            return MarketSnapshot(
                symbol=symbol,
                last_price=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One instrument master unavailable",
            )

        instrument = self._index_instrument(symbol)
        if not instrument:
            return MarketSnapshot(
                symbol=symbol,
                last_price=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=f"Angel One index mapping unavailable for {symbol}",
            )

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
        instruments = await self.get_instruments(symbol)
        today = datetime.now(timezone.utc).date()
        expiries = sorted({item.expiry for item in instruments if item.expiry and item.expiry >= today})

        if not expiries:
            return ExpiryInfo(
                symbol=symbol,
                expiries=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One expiry metadata unavailable",
            )

        nearest = expiries[0]
        next_expiry = expiries[1] if len(expiries) > 1 else None
        month_bucket = [exp for exp in expiries if exp.month == nearest.month and exp.year == nearest.year]
        monthly = month_bucket[-1] if month_bucket else nearest

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
                message="Angel One option strike metadata unavailable",
            )

        atm = min(strikes, key=lambda strike: abs(strike - quote.last_price))
        per_strike: dict[float, dict[str, Instrument]] = defaultdict(dict)
        for item in selected:
            if item.strike is None or not item.option_type:
                continue
            per_strike[item.strike][item.option_type] = item

        nearby_strikes = sorted(per_strike.keys(), key=lambda strike: abs(strike - atm))[:21]
        contracts: list[dict[str, object]] = []
        populated_legs = 0
        for strike in sorted(nearby_strikes):
            for option_type in ("CE", "PE"):
                inst = per_strike[strike].get(option_type)
                if not inst or not inst.instrument_token or not inst.trading_symbol or not inst.exchange:
                    continue
                ltp_data = await self._ltp(inst.exchange, inst.trading_symbol, inst.instrument_token)
                contract = {
                    "symbol": inst.trading_symbol,
                    "strike": strike,
                    "option_type": option_type,
                    "ltp": float(ltp_data.get("ltp")) if ltp_data and ltp_data.get("ltp") is not None else None,
                    "volume": int(float(ltp_data.get("tradeVolume", 0))) if ltp_data and ltp_data.get("tradeVolume") not in (None, "") else None,
                }
                if ltp_data:
                    populated_legs += 1
                contracts.append(contract)

        if not contracts or populated_legs == 0:
            return OptionChain(
                symbol=symbol,
                expiry=selected_expiry,
                underlying_price=quote.last_price,
                atm_strike=atm,
                distance_from_spot=round(quote.last_price - atm, 2),
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One option market data unavailable for selected expiry",
            )

        chain = normalize_option_chain(
            contracts,
            symbol=symbol,
            expiry=selected_expiry,
            source=self.name,
            underlying_price=quote.last_price,
        )
        return chain
