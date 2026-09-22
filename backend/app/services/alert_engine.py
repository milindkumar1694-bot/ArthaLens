import logging
from datetime import datetime, timezone, timedelta
from app.config import Settings
from app.services.telegram_alert import TelegramAlertService

logger = logging.getLogger("arthalens.alerts")

class AlertEngine:
    def __init__(self, settings: Settings, telegram_service: TelegramAlertService):
        self.settings = settings
        self.telegram_service = telegram_service
        self.cooldown_minutes = 5
        self._history: dict[str, datetime] = {}

    def _should_fire(self, rule_key: str) -> bool:
        now = datetime.now(timezone.utc)
        last_fired = self._history.get(rule_key)
        if last_fired and (now - last_fired) < timedelta(minutes=self.cooldown_minutes):
            return False
        self._history[rule_key] = now
        return True

    async def evaluate_and_dispatch(self, symbol: str, net_gex: float, cas_div: float | None, spot: float | None, flip_lvl: float | None, vix_chg: float | None):
        alerts_triggered = []

        if net_gex < 0 and self._should_fire(f"{symbol}:gex_negative"):
            title = f"{symbol} Net GEX Negative"
            msg = f"Net GEX flipped to {net_gex} ₹Cr — Short Gamma squeeze risk active."
            alerts_triggered.append((title, msg, "CRITICAL"))
            await self.telegram_service.send_alert(title, msg, "CRITICAL")

        if cas_div is not None and cas_div > 0.3 and self._should_fire(f"{symbol}:cas_divergence"):
            title = f"{symbol} CAS Divergence High"
            msg = f"Closing Auction Session divergence reached {cas_div}% (Threshold >0.3%)."
            alerts_triggered.append((title, msg, "CRITICAL"))
            await self.telegram_service.send_alert(title, msg, "CRITICAL")

        if spot and flip_lvl and abs(spot - flip_lvl) / spot < 0.002 and self._should_fire(f"{symbol}:gamma_flip_near"):
            title = f"{symbol} Near Gamma Flip"
            msg = f"Spot price ({spot}) within 0.2% of Gamma Flip level ({flip_lvl})."
            alerts_triggered.append((title, msg, "HIGH"))
            await self.telegram_service.send_alert(title, msg, "HIGH")

        if vix_chg is not None and vix_chg > 5.0 and self._should_fire("INDIAVIX:spike"):
            title = "India VIX Volatility Spike"
            msg = f"India VIX expanded +{vix_chg}% intraday."
            alerts_triggered.append((title, msg, "HIGH"))
            await self.telegram_service.send_alert(title, msg, "HIGH")

        return alerts_triggered
