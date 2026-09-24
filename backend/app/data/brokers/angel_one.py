import asyncio
import binascii
import logging
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Iterable

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
    """
    Production Angel One SmartAPI adapter.

    Responsibilities:
    - Authenticate with Angel One using a TOTP secret.
    - Resolve instruments from the official instrument master.
    - Fetch live market data from Angel One's Market Data API.
    - Build normalized option-chain data from real instruments/quotes.
    - Never fabricate market values.
    """

    name = "angelone"

    _AUTH_URL = (
        "https://apiconnect.angelone.in/"
        "rest/auth/angelbroking/user/v1/loginByPassword"
    )

    _MARKET_DATA_URL = (
        "https://apiconnect.angelone.in/"
        "rest/secure/angelbroking/market/v1/quote/"
    )

    _OPTION_GREEK_URL = (
        "https://apiconnect.angelone.in/"
        "rest/secure/angelbroking/marketData/v1/optionGreek"
    )

    _INDEX_ALIASES: dict[str, set[str]] = {
        "NIFTY": {
            "NIFTY",
            "NIFTY50",
            "NIFTY 50",
        },
        "BANKNIFTY": {
            "BANKNIFTY",
            "NIFTYBANK",
            "NIFTY BANK",
        },
        "SENSEX": {
            "SENSEX",
        },
        "INDIAVIX": {
            "INDIAVIX",
            "INDIA VIX",
            "VIX",
        },
    }

    def __init__(self, settings: Settings):
        self.settings = settings

        self.api_key = settings.angel_one_api_key.strip()
        self.client_id = settings.angel_one_client_id.strip()
        self.password = settings.angel_one_password.strip()
        self.totp_secret = settings.angel_one_totp.strip()

        self.instrument_master_url = (
            settings.angel_one_instrument_master_url.strip()
        )

        self.jwt_token: str | None = None
        self.feed_token: str | None = None

        self.connected = False
        self.authentication_attempted = False
        self.last_auth_reason: str | None = None
        self.last_auth_http_status: int | None = None
        self.last_success_at: datetime | None = None

        self._http_client: httpx.AsyncClient | None = None
        self._auth_lock = asyncio.Lock()

        self._instrument_master_rows: list[dict] = []
        self._instrument_master_loaded_at: datetime | None = None

        self._last_market_error: str | None = None

    # ------------------------------------------------------------------
    # Configuration / state
    # ------------------------------------------------------------------

    @property
    def _configuration_complete(self) -> bool:
        return bool(
            self.api_key
            and self.client_id
            and self.password
            and self.totp_secret
        )

    def _clear_auth(self, reason: str | None = None) -> None:
        self.connected = False
        self.jwt_token = None
        self.feed_token = None
        self.last_auth_reason = reason

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    async def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(15.0)
            )
        return self._http_client

    async def disconnect(self) -> None:
        self._clear_auth("disconnected")

        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    # ------------------------------------------------------------------
    # Headers / authentication
    # ------------------------------------------------------------------

    def _common_headers(self) -> dict[str, str]:
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

    def _auth_headers(self) -> dict[str, str]:
        return self._common_headers()

    def _market_headers(self) -> dict[str, str]:
        headers = self._common_headers()

        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        return headers

    def _auth_diagnostics(self) -> dict[str, bool]:
        return {
            "angelone_auth_attempt": True,
            "client_id_present": bool(self.client_id),
            "api_key_present": bool(self.api_key),
            "password_present": bool(self.password),
            "totp_present": bool(self.totp_secret),
        }

    def _generate_totp(self) -> str | None:
        """
        ANGEL_ONE_TOTP must contain the TOTP secret, not a permanent OTP code.
        """
        if not self.totp_secret:
            return None

        normalized_secret = (
            self.totp_secret.replace(" ", "").strip().upper()
        )

        try:
            return pyotp.TOTP(normalized_secret).now()
        except (binascii.Error, TypeError, ValueError):
            return None

    async def connect(self, force: bool = False) -> None:
        """
        Authenticate with Angel One.

        force=True is used only for controlled session re-authentication.
        """
        if self.connected and self.jwt_token and not force:
            return

        async with self._auth_lock:
            if self.connected and self.jwt_token and not force:
                return

            self.authentication_attempted = True

            diagnostics = self._auth_diagnostics()

            logger.info(
                "Angel One authentication attempt "
                "angelone_auth_attempt=%s "
                "client_id_present=%s "
                "api_key_present=%s "
                "password_present=%s "
                "totp_present=%s",
                diagnostics["angelone_auth_attempt"],
                diagnostics["client_id_present"],
                diagnostics["api_key_present"],
                diagnostics["password_present"],
                diagnostics["totp_present"],
            )

            if not self._configuration_complete:
                self._clear_auth("missing_credentials")
                logger.warning(
                    "Angel One authentication skipped: "
                    "required credentials incomplete"
                )
                return

            totp_code = self._generate_totp()

            if not totp_code:
                self._clear_auth("invalid_totp_configuration")
                logger.warning(
                    "Angel One authentication skipped: "
                    "invalid TOTP configuration; "
                    "ANGEL_ONE_TOTP must contain the TOTP secret"
                )
                return

            payload = {
                "clientcode": self.client_id,
                "password": self.password,
                "totp": totp_code,
            }

            try:
                client = await self._client()

                response = await client.post(
                    self._AUTH_URL,
                    json=payload,
                    headers=self._auth_headers(),
                )

                self.last_auth_http_status = response.status_code

                data = (
                    response.json()
                    if response.content
                    else {}
                )

                status_value = data.get("status")
                error_code = data.get("errorcode")
                message = data.get("message")

                auth_data = (
                    data.get("data")
                    if isinstance(data, dict)
                    else None
                )

                jwt_token = (
                    auth_data.get("jwtToken")
                    if isinstance(auth_data, dict)
                    else None
                )

                feed_token = (
                    auth_data.get("feedToken")
                    if isinstance(auth_data, dict)
                    else None
                )

                if (
                    response.status_code == 200
                    and status_value is True
                    and jwt_token
                    and feed_token
                ):
                    self.jwt_token = str(jwt_token)
                    self.feed_token = str(feed_token)
                    self.connected = True
                    self.last_auth_reason = "success"
                    self.last_success_at = datetime.now(timezone.utc)

                    logger.info(
                        "Angel One authentication successful "
                        "provider_connected=%s",
                        self.connected,
                    )
                    return

                self._clear_auth("authentication_failed")

                logger.warning(
                    "Angel One authentication failed "
                    "http_status=%s "
                    "response_status=%s "
                    "errorcode=%s "
                    "message=%s "
                    "provider_connected=%s",
                    response.status_code,
                    status_value,
                    error_code,
                    message,
                    self.connected,
                )

            except httpx.HTTPError as exc:
                self._clear_auth("network_failure")

                logger.error(
                    "Angel One authentication HTTP error "
                    "provider_connected=%s error=%s",
                    self.connected,
                    exc,
                )

            except Exception as exc:
                self._clear_auth("unexpected_error")

                logger.exception(
                    "Angel One authentication unexpected error "
                    "provider_connected=%s error=%s",
                    self.connected,
                    exc,
                )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    async def status(self) -> ProviderStatus:
        if not self._configuration_complete:
            message = (
                "Angel One credentials incomplete: "
                "api_key/client_id/password/totp required"
            )
        elif self.connected:
            message = "Angel One SmartAPI authenticated"
        elif self.authentication_attempted:
            message = (
                "Angel One authentication failed or "
                "connection unavailable"
            )
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

    # ------------------------------------------------------------------
    # Instrument master
    # ------------------------------------------------------------------

    async def _load_instrument_master(
        self,
        force_refresh: bool = False,
    ) -> bool:
        if (
            not force_refresh
            and self._instrument_master_rows
            and self._instrument_master_loaded_at
        ):
            age = (
                datetime.now(timezone.utc)
                - self._instrument_master_loaded_at
            ).total_seconds()

            if age < self.settings.instrument_master_cache_seconds:
                return True

        if not self.instrument_master_url:
            logger.warning(
                "Angel One instrument master unavailable: "
                "instrument master URL missing"
            )
            return False

        try:
            client = await self._client()

            response = await client.get(
                self.instrument_master_url
            )

            if response.status_code != 200:
                logger.warning(
                    "Angel One instrument master load failed "
                    "http_status=%s",
                    response.status_code,
                )
                return False

            payload = response.json()

            if not isinstance(payload, list):
                logger.warning(
                    "Angel One instrument master load failed: "
                    "unexpected payload"
                )
                return False

            self._instrument_master_rows = [
                item
                for item in payload
                if isinstance(item, dict)
            ]

            self._instrument_master_loaded_at = (
                datetime.now(timezone.utc)
            )

            logger.info(
                "Angel One instrument master loaded rows=%s",
                len(self._instrument_master_rows),
            )

            return True

        except httpx.HTTPError as exc:
            logger.error(
                "Angel One instrument master HTTP error: %s",
                exc,
            )
            return False

        except Exception as exc:
            logger.exception(
                "Angel One instrument master unexpected error: %s",
                exc,
            )
            return False

    @staticmethod
    def _normalize_symbol_text(value: object) -> str:
        if value is None:
            return ""

        return re.sub(
            r"[^A-Z0-9]",
            "",
            str(value).upper(),
        )

    @staticmethod
    def _canonical_exchange(value: object) -> str:
        raw = str(value or "").strip().upper()
        raw = raw.replace("-", "_")

        if raw in {
            "NSE",
            "NSE_CM",
            "NSECM",
            "NSE_IDX",
            "NSE_INDEX",
        }:
            return "NSE"

        if raw in {
            "NFO",
            "NSE_FO",
            "NSEFO",
        }:
            return "NFO"

        if raw in {
            "BSE",
            "BSE_CM",
            "BSECM",
            "BSE_IDX",
            "BSE_INDEX",
        }:
            return "BSE"

        if raw in {
            "BFO",
            "BSE_FO",
            "BSEFO",
        }:
            return "BFO"

        if raw.startswith("MCX"):
            return "MCX"

        return raw

    def _index_instrument(self, symbol: str) -> dict | None:
        """
        Resolve an actual index instrument from the official
        instrument master.

        Exact name/symbol matching is used to avoid accidentally
        matching equities such as NIFTYBEES.
        """
        symbol = symbol.upper()

        aliases = self._INDEX_ALIASES.get(
            symbol,
            {symbol},
        )

        alias_tokens = {
            self._normalize_symbol_text(alias)
            for alias in aliases
        }

        candidates: list[tuple[int, dict]] = []

        for row in self._instrument_master_rows:
            exchange = self._canonical_exchange(
                row.get("exch_seg")
            )

            if exchange not in {"NSE", "BSE"}:
                continue

            row_symbol = self._normalize_symbol_text(
                row.get("symbol")
            )

            row_name = self._normalize_symbol_text(
                row.get("name")
            )

            row_trading_symbol = self._normalize_symbol_text(
                row.get("tradingsymbol")
            )

            exact_match = (
                row_symbol in alias_tokens
                or row_name in alias_tokens
                or row_trading_symbol in alias_tokens
            )

            if not exact_match:
                continue

            token = str(row.get("token") or "").strip()

            if not token:
                continue

            instrument_type = str(
                row.get("instrumenttype") or ""
            ).upper()

            score = 0

            if instrument_type == "AMXIDX":
                score += 100

            if row_name in alias_tokens:
                score += 20

            if row_symbol in alias_tokens:
                score += 20

            if token.startswith("999"):
                score += 10

            candidates.append((score, row))

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        selected = candidates[0][1]

        logger.debug(
            "Angel One index resolved "
            "requested=%s exchange=%s symbol=%s token=%s",
            symbol,
            self._canonical_exchange(
                selected.get("exch_seg")
            ),
            selected.get("symbol"),
            selected.get("token"),
        )

        return selected

    # ------------------------------------------------------------------
    # Generic parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _to_float(value: object) -> float | None:
        if value in (None, ""):
            return None

        try:
            result = float(value)
        except (TypeError, ValueError):
            return None

        return result

    @staticmethod
    def _to_int(value: object) -> int | None:
        if value in (None, ""):
            return None

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _parse_expiry(self, raw: object) -> date | None:
        if raw in (None, ""):
            return None

        text = str(raw).strip().upper()

        formats = (
            "%d%b%Y",
            "%d%b%y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
        )

        for fmt in formats:
            try:
                return datetime.strptime(
                    text,
                    fmt,
                ).date()
            except ValueError:
                continue

        return None

    def _parse_strike(self, raw: object) -> float | None:
        value = self._to_float(raw)

        if value is None or value <= 0:
            return None

        # Angel One option-master strike values are commonly
        # stored as strike*100.
        if value > 100000:
            value /= 100.0

        return value

    def _to_option_instrument(
        self,
        row: dict,
        symbol: str,
    ) -> Instrument | None:
        target = symbol.upper()

        exchange = self._canonical_exchange(
            row.get("exch_seg")
        )

        if exchange != "NFO":
            return None

        instrument_type = str(
            row.get("instrumenttype")
            or row.get("instrument_type")
            or ""
        ).upper()

        if "OPT" not in instrument_type:
            return None

        raw_symbol = str(
            row.get("symbol")
            or row.get("tradingsymbol")
            or ""
        ).strip()

        normalized_option_symbol = (
            self._normalize_symbol_text(raw_symbol)
        )

        normalized_target = (
            self._normalize_symbol_text(target)
        )

        row_name = self._normalize_symbol_text(
            row.get("name")
        )

        underlying_match = (
            row_name == normalized_target
            or normalized_option_symbol.startswith(
                normalized_target
            )
        )

        # Prevent NIFTY from accidentally matching BANKNIFTY.
        if (
            target == "NIFTY"
            and normalized_option_symbol.startswith(
                "BANKNIFTY"
            )
        ):
            underlying_match = False

        if not underlying_match:
            return None

        option_type: str | None = None

        if normalized_option_symbol.endswith("CE"):
            option_type = "CE"
        elif normalized_option_symbol.endswith("PE"):
            option_type = "PE"

        if option_type is None:
            return None

        expiry = self._parse_expiry(
            row.get("expiry")
        )

        strike = self._parse_strike(
            row.get("strike")
        )

        token = str(
            row.get("token") or ""
        ).strip()

        if not expiry or strike is None or not token:
            return None

        lot_size = self._to_int(
            row.get("lotsize")
        )

        return Instrument(
            symbol=raw_symbol,
            underlying=target,
            exchange=exchange,
            expiry=expiry,
            strike=strike,
            option_type=option_type,
            instrument_token=token,
            trading_symbol=raw_symbol,
            lot_size=lot_size,
            provider=self.name,
        )

    # ------------------------------------------------------------------
    # Live market-data API
    # ------------------------------------------------------------------

    async def _market_data_many(
        self,
        instruments: Iterable[Instrument],
        mode: str = "FULL",
        retry_auth: bool = True,
    ) -> dict[str, dict]:
        """
        Fetch live market data using Angel One's Market Data API.

        Returns:
            {symbol_token: fetched_row}
        """
        if not self.connected or not self.jwt_token:
            return {}

        grouped: defaultdict[str, list[str]] = defaultdict(list)

        for instrument in instruments:
            if (
                not instrument.exchange
                or not instrument.instrument_token
            ):
                continue

            exchange = self._canonical_exchange(
                instrument.exchange
            )

            token = str(
                instrument.instrument_token
            ).strip()

            if not token:
                continue

            if token not in grouped[exchange]:
                grouped[exchange].append(token)

        if not grouped:
            return {}

        payload = {
            "mode": mode,
            "exchangeTokens": dict(grouped),
        }

        self._last_market_error = None

        try:
            client = await self._client()

            response = await client.post(
                self._MARKET_DATA_URL,
                json=payload,
                headers=self._market_headers(),
            )

            data = (
                response.json()
                if response.content
                else {}
            )

            response_status = data.get(
                "status",
                data.get("success"),
            )

            error_code = data.get(
                "errorcode",
                data.get("errorCode"),
            )

            message = data.get("message")

            # Angel One docs indicate 401/403 for invalid/expired
            # authorization. Re-authenticate once and retry.
            if (
                response.status_code in {401, 403}
                or error_code == "AG8001"
            ):
                self._last_market_error = (
                    f"{error_code or 'AUTH_ERROR'}: "
                    f"{message or 'authorization failed'}"
                )

                self._clear_auth("session_expired")

                if retry_auth:
                    await self.connect(force=True)

                    if self.connected:
                        return await self._market_data_many(
                            instruments,
                            mode=mode,
                            retry_auth=False,
                        )

                return {}

            if response.status_code != 200:
                self._last_market_error = (
                    f"HTTP {response.status_code}: "
                    f"{message or 'market data request failed'}"
                )

                logger.warning(
                    "Angel One market data request failed "
                    "http_status=%s errorcode=%s message=%s",
                    response.status_code,
                    error_code,
                    message,
                )

                return {}

            if response_status is not True:
                self._last_market_error = (
                    f"{error_code or 'MARKET_DATA_ERROR'}: "
                    f"{message or 'market data request failed'}"
                )

                logger.warning(
                    "Angel One market data unavailable "
                    "http_status=%s status=%s errorcode=%s message=%s",
                    response.status_code,
                    response_status,
                    error_code,
                    message,
                )

                return {}

            container = data.get("data")

            if not isinstance(container, dict):
                self._last_market_error = (
                    "Market data response missing data object"
                )
                return {}

            fetched = container.get("fetched") or []
            unfetched = container.get("unfetched") or []

            if unfetched:
                logger.warning(
                    "Angel One market data unfetched_count=%s",
                    len(unfetched),
                )

            result: dict[str, dict] = {}

            for row in fetched:
                if not isinstance(row, dict):
                    continue

                token = str(
                    row.get("symbolToken")
                    or row.get("symboltoken")
                    or ""
                ).strip()

                if token:
                    result[token] = row

            return result

        except httpx.HTTPError as exc:
            self._last_market_error = str(exc)

            logger.error(
                "Angel One market data HTTP error: %s",
                exc,
            )
            return {}

        except Exception as exc:
            self._last_market_error = str(exc)

            logger.exception(
                "Angel One market data unexpected error: %s",
                exc,
            )
            return {}

    # ------------------------------------------------------------------
    # Quote
    # ------------------------------------------------------------------

    async def get_quote(
        self,
        symbol: str,
    ) -> MarketSnapshot:
        symbol = symbol.upper()

        if not self.connected:
            await self.connect()

        if not self.connected:
            return MarketSnapshot(
                symbol=symbol,
                last_price=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One authentication failed or "
                    "connection unavailable"
                ),
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
                message=(
                    f"Angel One index mapping unavailable "
                    f"for {symbol}"
                ),
            )

        exchange = self._canonical_exchange(
            instrument.get("exch_seg")
        )

        trading_symbol = str(
            instrument.get("symbol")
            or instrument.get("tradingsymbol")
            or ""
        ).strip()

        token = str(
            instrument.get("token")
            or ""
        ).strip()

        if not trading_symbol or not token:
            return MarketSnapshot(
                symbol=symbol,
                exchange=exchange,
                last_price=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    f"Angel One token mapping incomplete "
                    f"for {symbol}"
                ),
            )

        resolved = Instrument(
            symbol=trading_symbol,
            underlying=symbol,
            exchange=exchange,
            instrument_token=token,
            trading_symbol=trading_symbol,
            provider=self.name,
        )

        logger.debug(
            "Angel One quote request symbol=%s "
            "exchange=%s instrument_resolved=%s token_present=%s",
            symbol,
            exchange,
            True,
            bool(token),
        )

        market_data = await self._market_data_many(
            [resolved],
            mode="FULL",
        )

        quote_data = market_data.get(token)

        if not quote_data:
            return MarketSnapshot(
                symbol=symbol,
                exchange=exchange,
                last_price=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One live quote feed currently "
                    "unavailable"
                    + (
                        f": {self._last_market_error}"
                        if self._last_market_error
                        else ""
                    )
                ),
            )

        ltp = self._to_float(
            quote_data.get("ltp")
        )

        close = self._to_float(
            quote_data.get("close")
        )

        open_price = self._to_float(
            quote_data.get("open")
        )

        high = self._to_float(
            quote_data.get("high")
        )

        low = self._to_float(
            quote_data.get("low")
        )

        volume = self._to_int(
            quote_data.get("tradeVolume")
        )

        if ltp is None or ltp <= 0:
            return MarketSnapshot(
                symbol=symbol,
                exchange=exchange,
                last_price=None,
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Angel One returned no usable LTP",
            )

        change = self._to_float(
            quote_data.get("netChange")
        )

        percent_change = self._to_float(
            quote_data.get("percentChange")
        )

        if change is None and close not in (None, 0):
            change = round(ltp - close, 2)

        if (
            percent_change is None
            and change is not None
            and close not in (None, 0)
        ):
            percent_change = round(
                change / close * 100.0,
                3,
            )

        # Index volume may legitimately be zero/not meaningful.
        # Do not invent another value.
        return MarketSnapshot(
            symbol=symbol,
            exchange=exchange,
            last_price=ltp,
            change=change,
            change_percent=percent_change,
            open=open_price,
            high=high,
            low=low,
            previous_close=close,
            volume=volume,
            timestamp=datetime.now(timezone.utc),
            source=self.name,
            status=Status.OK,
            market_status="OPEN",
        )

    # ------------------------------------------------------------------
    # Option instruments
    # ------------------------------------------------------------------

    async def get_instruments(
        self,
        symbol: str | None = None,
    ) -> list[Instrument]:
        loaded = await self._load_instrument_master()

        if not loaded:
            return []

        targets = (
            [symbol.upper()]
            if symbol
            else ["NIFTY", "BANKNIFTY"]
        )

        instruments: list[Instrument] = []

        for target in targets:
            for row in self._instrument_master_rows:
                instrument = self._to_option_instrument(
                    row,
                    target,
                )

                if instrument:
                    instruments.append(instrument)

        instruments.sort(
            key=lambda item: (
                item.expiry or date.max,
                item.strike or 0.0,
                item.option_type or "",
            )
        )

        return instruments

    # ------------------------------------------------------------------
    # Expiries
    # ------------------------------------------------------------------

    async def get_expiries(
        self,
        symbol: str,
    ) -> ExpiryInfo:
        symbol = symbol.upper()

        if symbol not in {"NIFTY", "BANKNIFTY"}:
            return ExpiryInfo(
                symbol=symbol,
                expiries=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Unsupported option underlying"
                ),
            )

        instruments = await self.get_instruments(
            symbol
        )

        today = datetime.now(
            timezone.utc
        ).date()

        expiries = sorted(
            {
                item.expiry
                for item in instruments
                if item.expiry
                and item.expiry >= today
            }
        )

        if not expiries:
            return ExpiryInfo(
                symbol=symbol,
                expiries=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One expiry metadata unavailable"
                ),
            )

        nearest = expiries[0]

        next_expiry = (
            expiries[1]
            if len(expiries) > 1
            else None
        )

        monthly_candidates = [
            expiry
            for expiry in expiries
            if expiry.month == nearest.month
            and expiry.year == nearest.year
        ]

        monthly = (
            monthly_candidates[-1]
            if monthly_candidates
            else nearest
        )

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

    # ------------------------------------------------------------------
    # Option Greeks
    # ------------------------------------------------------------------

    async def _get_option_greeks(
        self,
        symbol: str,
        expiry: date,
    ) -> dict[tuple[float, str], dict]:
        if not self.connected or not self.jwt_token:
            return {}

        expiry_text = expiry.strftime(
            "%d%b%Y"
        ).upper()

        payload = {
            "name": symbol.upper(),
            "expirydate": expiry_text,
        }

        try:
            client = await self._client()

            response = await client.post(
                self._OPTION_GREEK_URL,
                json=payload,
                headers=self._market_headers(),
            )

            data = (
                response.json()
                if response.content
                else {}
            )

            if response.status_code in {401, 403}:
                self._clear_auth(
                    "session_expired"
                )
                return {}

            if (
                response.status_code != 200
                or data.get("status") is not True
            ):
                logger.warning(
                    "Angel One option Greek request unavailable "
                    "symbol=%s expiry=%s errorcode=%s message=%s",
                    symbol,
                    expiry_text,
                    data.get("errorcode"),
                    data.get("message"),
                )
                return {}

            raw_rows = data.get("data")

            if not isinstance(raw_rows, list):
                return {}

            result: dict[tuple[float, str], dict] = {}

            for row in raw_rows:
                if not isinstance(row, dict):
                    continue

                strike = self._parse_strike(
                    row.get("strikePrice")
                )

                option_type = str(
                    row.get("optionType") or ""
                ).upper()

                if strike is None:
                    continue

                if option_type not in {"CE", "PE"}:
                    continue

                result[(strike, option_type)] = row

            return result

        except Exception as exc:
            logger.warning(
                "Angel One option Greek request failed "
                "symbol=%s expiry=%s error=%s",
                symbol,
                expiry_text,
                exc,
            )
            return {}

    # ------------------------------------------------------------------
    # Option chain
    # ------------------------------------------------------------------

    async def get_option_chain(
        self,
        symbol: str,
        expiry: str | None = None,
    ) -> OptionChain:
        symbol = symbol.upper()

        if symbol not in {"NIFTY", "BANKNIFTY"}:
            return OptionChain(
                symbol=symbol,
                strikes=[],
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                status=Status.UNAVAILABLE,
                message=(
                    "Unsupported option underlying"
                ),
            )

        if not self.connected:
            await self.connect()

        if not self.connected:
            return OptionChain(
                symbol=symbol,
                expiry=self._parse_expiry(expiry),
                underlying_price=None,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One authentication failed "
                    "or connection unavailable"
                ),
            )

        quote = await self.get_quote(symbol)

        if (
            quote.status != Status.OK
            or quote.last_price is None
        ):
            return OptionChain(
                symbol=symbol,
                expiry=self._parse_expiry(expiry),
                underlying_price=None,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One live underlying quote unavailable"
                ),
            )

        instruments = await self.get_instruments(
            symbol
        )

        if not instruments:
            return OptionChain(
                symbol=symbol,
                underlying_price=quote.last_price,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One option instruments unavailable"
                ),
            )

        available_expiries = sorted(
            {
                item.expiry
                for item in instruments
                if item.expiry
            }
        )

        if not available_expiries:
            return OptionChain(
                symbol=symbol,
                underlying_price=quote.last_price,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One option expiry metadata unavailable"
                ),
            )

        selected_expiry = (
            self._parse_expiry(expiry)
            if expiry
            else available_expiries[0]
        )

        if selected_expiry is None:
            return OptionChain(
                symbol=symbol,
                underlying_price=quote.last_price,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message="Invalid expiry format",
            )

        selected = [
            item
            for item in instruments
            if item.expiry == selected_expiry
        ]

        if not selected:
            return OptionChain(
                symbol=symbol,
                expiry=selected_expiry,
                underlying_price=quote.last_price,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One option instruments unavailable "
                    f"for expiry {selected_expiry.isoformat()}"
                ),
            )

        strikes = sorted(
            {
                item.strike
                for item in selected
                if item.strike is not None
            }
        )

        if not strikes:
            return OptionChain(
                symbol=symbol,
                expiry=selected_expiry,
                underlying_price=quote.last_price,
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One option strike metadata unavailable"
                ),
            )

        atm = min(
            strikes,
            key=lambda strike: abs(
                strike - quote.last_price
            ),
        )

        per_strike: dict[
            float,
            dict[str, Instrument],
        ] = defaultdict(dict)

        for instrument in selected:
            if (
                instrument.strike is None
                or not instrument.option_type
            ):
                continue

            per_strike[
                instrument.strike
            ][instrument.option_type] = instrument

        # 21 strikes * 2 legs = max 42 tokens,
        # comfortably within the current 50-token market-data limit.
        nearby_strikes = sorted(
            per_strike.keys(),
            key=lambda strike: abs(
                strike - atm
            ),
        )[:21]

        selected_contracts: list[Instrument] = []

        for strike in nearby_strikes:
            for option_type in ("CE", "PE"):
                instrument = per_strike[strike].get(
                    option_type
                )

                if instrument:
                    selected_contracts.append(
                        instrument
                    )

        market_data = await self._market_data_many(
            selected_contracts,
            mode="FULL",
        )

        greek_data = await self._get_option_greeks(
            symbol,
            selected_expiry,
        )

        contracts: list[dict[str, object]] = []

        fetched_count = 0

        for instrument in selected_contracts:
            token = str(
                instrument.instrument_token
            ).strip()

            quote_data = market_data.get(token)

            if quote_data:
                fetched_count += 1

            greek = greek_data.get(
                (
                    float(instrument.strike),
                    str(
                        instrument.option_type
                    ).upper(),
                )
            )

            ltp = (
                self._to_float(
                    quote_data.get("ltp")
                )
                if quote_data
                else None
            )

            volume = (
                self._to_int(
                    quote_data.get("tradeVolume")
                )
                if quote_data
                else None
            )

            oi = (
                self._to_int(
                    quote_data.get("opnInterest")
                )
                if quote_data
                else None
            )

            bid = None
            ask = None

            depth = (
                quote_data.get("depth")
                if quote_data
                else None
            )

            if isinstance(depth, dict):
                buys = depth.get("buy") or []
                sells = depth.get("sell") or []

                if buys and isinstance(buys[0], dict):
                    bid = self._to_float(
                        buys[0].get("price")
                    )

                if sells and isinstance(sells[0], dict):
                    ask = self._to_float(
                        sells[0].get("price")
                    )

            iv = (
                self._to_float(
                    greek.get(
                        "impliedVolatility"
                    )
                )
                if greek
                else None
            )

            contracts.append(
                {
                    "symbol": instrument.trading_symbol,
                    "strike": instrument.strike,
                    "option_type": instrument.option_type,
                    "oi": oi,
                    "volume": volume,
                    "iv": iv,
                    "ltp": ltp,
                    "bid": bid,
                    "ask": ask,
                }
            )

        if not contracts or fetched_count == 0:
            return OptionChain(
                symbol=symbol,
                expiry=selected_expiry,
                underlying_price=quote.last_price,
                atm_strike=atm,
                distance_from_spot=round(
                    quote.last_price - atm,
                    2,
                ),
                strikes=[],
                status=Status.UNAVAILABLE,
                source=self.name,
                timestamp=datetime.now(timezone.utc),
                message=(
                    "Angel One option market data "
                    "unavailable for selected expiry"
                ),
            )

        chain = normalize_option_chain(
            contracts,
            symbol=symbol,
            expiry=selected_expiry,
            source=self.name,
            underlying_price=quote.last_price,
        )

        expected_count = len(selected_contracts)

        if (
            expected_count > 0
            and fetched_count < expected_count
            and chain.status == Status.OK
        ):
            chain = chain.model_copy(
                update={
                    "status": Status.PARTIAL,
                    "message": (
                        f"{expected_count - fetched_count} "
                        "option quotes were unavailable"
                    ),
                }
            )

        return chain
