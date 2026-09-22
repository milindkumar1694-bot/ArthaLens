from datetime import datetime, timezone, date
from fastapi import APIRouter, HTTPException, Request
from app.analytics.cas_monitor import check_cas_window
from app.schemas.expiry import (
    ExpiryIntelPayload, GammaStrikeProfile, DealerHedgingEstimate,
    ExpiryProbabilityScore, HistoricalExpiryPattern
)

router = APIRouter(prefix="/expiry", tags=["expiry"])

@router.get("/{symbol}", response_model=ExpiryIntelPayload, summary="Expiry intelligence, GEX regime & CAS monitor")
async def get_expiry_intelligence(symbol: str, request: Request, expiry: str | None = None):
    try:
        is_live = (request.app.state.settings.data_mode == "live")
        chain = await request.app.state.market_service.option_chain(symbol, expiry)
        analytics = await request.app.state.analytics_service.calculate(chain)
        
        gex_data = analytics.get("gex", {})
        net_gex = gex_data.get("value") or 0.0
        regime = "Pinning" if net_gex > 0 else ("Squeeze" if net_gex < 0 else "Neutral")
        violence_prob = "LOW" if net_gex > 5000 else ("HIGH" if net_gex < -2000 else "MEDIUM")
        
        pin_target = gex_data.get("pin_target") or chain.atm_strike
        spot = chain.underlying_price
        
        gamma_profiles = []
        raw_profiles = gex_data.get("profile", [])
        if raw_profiles:
            for item in raw_profiles:
                gamma_profiles.append(GammaStrikeProfile(
                    strike=item["strike"],
                    gex=item["gex"],
                    is_pin_target=(pin_target is not None and item["strike"] == pin_target),
                    is_gamma_wall=(abs(item["gex"]) > 1000)
                ))
        elif not is_live and spot:
            # Fallback profiles around spot ONLY in mock mode
            base_strike = round(spot / 50) * 50
            for offset in range(-250, 300, 50):
                stk = base_strike + offset
                val = round((100 - abs(offset)) * 25.5, 2)
                gamma_profiles.append(GammaStrikeProfile(
                    strike=stk,
                    gex=val,
                    is_pin_target=(pin_target is not None and stk == pin_target),
                    is_gamma_wall=(stk in [base_strike - 200, base_strike + 200])
                ))

        cas_status = check_cas_window(spot, is_live_mode=is_live)
        flip_lvl = gex_data.get("gamma_flip")

        dealer_est = DealerHedgingEstimate(
            net_gex=net_gex,
            dealer_position="Long Gamma" if net_gex > 0 else ("Short Gamma" if net_gex < 0 else "Neutral"),
            hedging_direction="Sell Rallies / Buy Dips" if net_gex > 0 else ("Buy Rallies / Sell Dips" if net_gex < 0 else "Balanced"),
            gamma_flip_level=flip_lvl,
            distance_to_flip=round(spot - flip_lvl, 2) if (spot and flip_lvl) else None
        )

        prob_score = ExpiryProbabilityScore(
            pinning_probability=68.5 if net_gex > 0 else (25.0 if net_gex < 0 else 33.3),
            squeeze_probability=21.5 if net_gex > 0 else (60.0 if net_gex < 0 else 33.3),
            breakout_probability=10.0 if net_gex > 0 else (15.0 if net_gex < 0 else 33.4),
            primary_factor="Net GEX is positive with heavy OI concentration near Max Pain" if net_gex > 0 else ("Negative Net GEX with dealer short gamma acceleration risk" if net_gex < 0 else "GEX neutral")
        )

        hist_patterns = []
        if not is_live:
            # Historical reference records only present in mock mode
            hist_patterns = [
                HistoricalExpiryPattern(
                    date=date(2024, 3, 21),
                    symbol=symbol.upper(),
                    net_gex_regime="Pinning",
                    violence_occurred=False,
                    max_intraday_move_pts=42.5,
                    max_intraday_move_pct=0.19,
                    pin_target_hit=True
                ),
                HistoricalExpiryPattern(
                    date=date(2024, 3, 14),
                    symbol=symbol.upper(),
                    net_gex_regime="Squeeze",
                    violence_occurred=True,
                    max_intraday_move_pts=218.0,
                    max_intraday_move_pct=0.97,
                    pin_target_hit=False
                )
            ]

        alerts = []
        if net_gex < 0:
            alerts.append("CRITICAL: Net GEX is negative — Short Gamma squeeze risk active.")
        if cas_status.alert_triggered:
            alerts.append(f"CRITICAL: CAS Divergence > 0.3% ({cas_status.divergence_percent}%).")
        if spot and flip_lvl and abs(spot - flip_lvl) / spot < 0.002:
            alerts.append("HIGH: Spot within 0.2% of Gamma Flip level.")

        return ExpiryIntelPayload(
            symbol=symbol.upper(),
            expiry=chain.expiry,
            timestamp=datetime.now(timezone.utc),
            status=chain.status,
            net_gex=net_gex,
            regime=regime,
            violence_probability=violence_prob,
            pin_target_strike=pin_target,
            expected_range_lower=(spot - 120.0) if spot else None,
            expected_range_upper=(spot + 120.0) if spot else None,
            gamma_profile=gamma_profiles,
            dealer_hedging=dealer_est,
            probability_score=prob_score,
            cas_monitor=cas_status,
            historical_comparison=hist_patterns,
            alerts=alerts
        )
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err)) from err
