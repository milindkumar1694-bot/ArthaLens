from datetime import datetime, timezone
import zoneinfo
from app.schemas.expiry import CasWindowMonitor

def check_cas_window(spot_price: float | None = None, indicative_close: float | None = None, is_live_mode: bool = False) -> CasWindowMonitor:
    try:
        ist = zoneinfo.ZoneInfo("Asia/Kolkata")
        now_ist = datetime.now(ist)
    except Exception:
        now_ist = datetime.now(timezone.utc)

    # 3:15 PM to 3:40 PM IST
    active = (now_ist.hour == 15 and 15 <= now_ist.minute <= 40)
    
    if spot_price is not None and indicative_close is not None and spot_price > 0:
        div_pct = round(abs(indicative_close - spot_price) / spot_price * 100.0, 3)
        if div_pct > 0.3:
            status = "EXTREME"
            alert = True
        elif div_pct > 0.15:
            status = "ELEVATED"
            alert = False
        else:
            status = "NORMAL"
            alert = False

        return CasWindowMonitor(
            active_window=active,
            indicative_close=indicative_close,
            regular_close=spot_price,
            divergence_percent=div_pct,
            status=status,
            alert_triggered=alert
        )

    if is_live_mode:
        # In live mode, without live indicative close tick feed, return UNAVAILABLE without fabricating 0.12%
        return CasWindowMonitor(
            active_window=active,
            indicative_close=None,
            regular_close=spot_price,
            divergence_percent=None,
            status="UNAVAILABLE",
            alert_triggered=False
        )

    # In development/mock mode, provide deterministic simulation
    div_pct = 0.12
    return CasWindowMonitor(
        active_window=active,
        indicative_close=spot_price + 8.5 if spot_price else 22548.75,
        regular_close=spot_price or 22540.25,
        divergence_percent=div_pct,
        status="NORMAL",
        alert_triggered=False
    )
