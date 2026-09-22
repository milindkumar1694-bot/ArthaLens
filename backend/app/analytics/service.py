from datetime import datetime, timezone
from app.analytics.expiry import calculate_expiry
from app.analytics.gex import calculate_gex
from app.analytics.greeks import calculate_greeks
from app.analytics.max_pain import calculate_max_pain
from app.analytics.oi_levels import calculate_oi_levels
from app.analytics.pcr import calculate_pcr
from app.analytics.unusual_activity import calculate_unusual_activity
from app.config import Settings
from app.schemas.common import Status
from app.schemas.options import OptionChain
from app.services.cache import Cache

class AnalyticsService:
    def __init__(self, settings: Settings, cache: Cache): self.settings = settings; self.cache = cache
    async def calculate(self, chain: OptionChain, strike_range: int | None = None) -> dict:
        key = f"analytics:{chain.symbol}:{chain.expiry}:{strike_range or 'all'}"; cached = await self.cache.get(key, AnalyticsPayload)
        if cached: return cached.model_dump()
        if chain.status in {Status.UNAVAILABLE, Status.ERROR}:
            return AnalyticsPayload(symbol=chain.symbol, expiry=chain.expiry, status=chain.status, timestamp=datetime.now(timezone.utc), reason=chain.message).model_dump()
        pcr = calculate_pcr(chain); ranged = calculate_pcr(chain, strike_range) if strike_range else None; pain = calculate_max_pain(chain); days = calculate_expiry(chain, pain["strike"])["days"]
        atm = next((r for r in chain.strikes if r.strike == chain.atm_strike), None)
        ce_g = calculate_greeks(chain.underlying_price, atm.strike, atm.ce.iv if atm and atm.ce else None, days or 0, True, self.settings.risk_free_rate, self.settings.dividend_yield) if atm else None
        pe_g = calculate_greeks(chain.underlying_price, atm.strike, atm.pe.iv if atm and atm.pe else None, days or 0, False, self.settings.risk_free_rate, self.settings.dividend_yield) if atm else None
        atm_iv = round(((atm.ce.iv if atm and atm.ce and atm.ce.iv is not None else 0)+(atm.pe.iv if atm and atm.pe and atm.pe.iv is not None else 0))/2, 4) if atm and atm.ce and atm.pe and atm.ce.iv is not None and atm.pe.iv is not None else None
        gex = calculate_gex(chain, days or 0, self.settings.risk_free_rate, self.settings.default_lot_size)
        payload = AnalyticsPayload(symbol=chain.symbol, expiry=chain.expiry, timestamp=datetime.now(timezone.utc), status=chain.status, underlying={"price":chain.underlying_price,"atm_strike":chain.atm_strike,"distance":chain.distance_from_spot}, pcr={**pcr, "oi_range": ranged["oi"] if ranged else None, "volume_range": ranged["volume"] if ranged else None}, oi_levels=calculate_oi_levels(chain), max_pain=pain, iv={"atm":atm_iv,"percentile":None,"reason":"historical IV data unavailable"}, greeks={"ce":ce_g,"pe":pe_g,"model":"Black-Scholes","risk_free_rate":self.settings.risk_free_rate,"dividend_yield":self.settings.dividend_yield,"calculated_at":datetime.now(timezone.utc)}, gex=gex, gamma_flip={"level":gex["gamma_flip"],"current_gex":gex["value"],"distance_from_flip":round(chain.underlying_price-gex["gamma_flip"],2) if gex["gamma_flip"] and chain.underlying_price else None,"regime":gex["sign"]}, expiry_metrics=calculate_expiry(chain,pain["strike"]), unusual_activity=calculate_unusual_activity(chain), attention=[])
        await self.cache.set(key, payload, self.settings.option_chain_cache_ttl_seconds); return payload.model_dump()

from pydantic import BaseModel
from datetime import date
class AnalyticsPayload(BaseModel):
    symbol: str; expiry: date | None = None; timestamp: datetime; status: Status; reason: str | None = None
    underlying: dict = {}; pcr: dict = {}; oi_levels: dict = {}; max_pain: dict = {}; iv: dict = {}; greeks: dict = {}; gex: dict = {}; gamma_flip: dict = {}; expiry_metrics: dict = {}; unusual_activity: list[dict] = []; attention: list[dict] = []
