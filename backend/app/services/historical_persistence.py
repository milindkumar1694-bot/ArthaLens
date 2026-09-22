import logging
from datetime import datetime, timezone, date
from app.config import Settings
from app.schemas.common import Status

logger = logging.getLogger("arthalens.historical")

class HistoricalPersistenceService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_url = settings.database_url
        # In-memory storage when DB URL is unconfigured
        self._iv_store: list[dict] = []
        self._expiry_store: list[dict] = []

    async def save_atm_iv(self, symbol: str, spot: float, atm_strike: float, iv: float):
        if not spot or not iv:
            return
        entry = {
            "symbol": symbol.upper(),
            "timestamp": datetime.now(timezone.utc),
            "spot": spot,
            "atm_strike": atm_strike,
            "iv": iv
        }
        self._iv_store.append(entry)
        logger.debug("Saved ATM IV snapshot for %s: %s", symbol, entry)

    async def get_iv_percentile(self, symbol: str, current_iv: float | None, window_days: int = 30) -> dict:
        if current_iv is None or not self.db_url:
            return {
                "percentile": None,
                "status": Status.UNAVAILABLE,
                "reason": "HISTORICAL IV DATA INSUFFICIENT"
            }
        
        filtered = [x["iv"] for x in self._iv_store if x["symbol"] == symbol.upper()]
        if len(filtered) < 5:
            return {
                "percentile": None,
                "status": Status.UNAVAILABLE,
                "reason": "HISTORICAL IV DATA INSUFFICIENT"
            }

        below_count = sum(1 for x in filtered if x < current_iv)
        percentile = round((below_count / len(filtered)) * 100.0, 2)
        return {
            "percentile": percentile,
            "status": Status.OK,
            "sample_size": len(filtered)
        }

    async def get_historical_expiries(self, symbol: str) -> dict:
        if not self.db_url:
            return {
                "status": Status.UNAVAILABLE,
                "reason": "Live historical expiry database persistence unconfigured",
                "items": []
            }
        return {
            "status": Status.OK,
            "items": self._expiry_store
        }
