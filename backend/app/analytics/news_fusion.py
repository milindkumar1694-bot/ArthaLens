from datetime import datetime, timezone
from app.schemas.news import NewsItem, NewsFusionResult, NewsResponsePayload
from app.schemas.options import OptionChain

MOCK_NEWS_ITEMS: list[NewsItem] = [
    NewsItem(
        id="news-01",
        headline="RBI Holds Repo Rate Unchanged at 6.50%; Maintains Hawkish Stance on Inflation",
        summary="RBI Monetary Policy Committee voted 5-1 to keep benchmark repo rate at 6.50% while reiterating commitment to bring inflation down to target 4%.",
        category="RBI",
        affected_asset="BANK NIFTY",
        direction="Mixed",
        importance="CRITICAL",
        iv_impact="Rising",
        affected_strikes=[
            {"strike": 48000, "option_type": "PE", "action": "PE Buy / CE Write"},
            {"strike": 48500, "option_type": "CE", "action": "Short Call Concentration"}
        ],
        expected_move_change=180.0,
        why_it_matters="Hawkish commentary puts pressure on rate-sensitive PSU and private banking sector options.",
        what_to_watch_next="Watch Bank Nifty 48,000 PE wall for buildup and Governor's Q&A presser.",
        confidence="High",
        timestamp=datetime.now(timezone.utc),
        source="curated"
    ),
    NewsItem(
        id="news-02",
        headline="US Fed Signals Potential Rate Cut in Upcoming FOMC Meeting as Inflation Moderates",
        summary="Federal Reserve Chair Powell indicated rate adjustments could come sooner than expected following softer CPI prints.",
        category="Fed",
        affected_asset="NIFTY",
        direction="Positive",
        importance="HIGH",
        iv_impact="Crush",
        affected_strikes=[
            {"strike": 22600, "option_type": "CE", "action": "CE Long / PE Unwind"}
        ],
        expected_move_change=-50.0,
        why_it_matters="Global liquidity boost favors IT and FMCG index heavyweights, leading to IV compression.",
        what_to_watch_next="Watch Nifty 22,500 Call wall breakout momentum.",
        confidence="High",
        timestamp=datetime.now(timezone.utc),
        source="curated"
    ),
    NewsItem(
        id="news-03",
        headline="FII Net Buyers of ₹3,420 Cr in Index Futures & Stock Options",
        summary="Foreign Institutional Investors turned strong net buyers in derivatives segment with heavy long building in Nifty Futures.",
        category="FII_DII",
        affected_asset="NIFTY",
        direction="Positive",
        importance="HIGH",
        iv_impact="Unchanged",
        affected_strikes=[
            {"strike": 22500, "option_type": "PE", "action": "PE Writing Support"}
        ],
        expected_move_change=90.0,
        why_it_matters="FII long-to-short ratio improved from 38% to 54%, establishing strong floor at 22,400.",
        what_to_watch_next="Expiry day gamma squeeze risk above 22,600.",
        confidence="High",
        timestamp=datetime.now(timezone.utc),
        source="curated"
    )
]

def analyze_news_fusion(chain: OptionChain | None, is_live_mode: bool = False, live_news_items: list[NewsItem] | None = None) -> NewsResponsePayload:
    if is_live_mode and not live_news_items:
        # In live mode without a live news provider stream, return UNAVAILABLE without leaking mock news
        return NewsResponsePayload(
            timestamp=datetime.now(timezone.utc),
            status="unavailable",
            categories=["RBI", "Budget", "Fed", "CPI", "Earnings", "FII_DII", "Geopolitical", "Crude_INR", "SEBI"],
            items=[],
            fusion_insights=[]
        )

    items = live_news_items if live_news_items else MOCK_NEWS_ITEMS
    fusion_results: list[NewsFusionResult] = []

    pcr_val = 1.05
    if chain and chain.strikes:
        total_ce_oi = sum(r.ce.oi or 0 for r in chain.strikes if r.ce)
        total_pe_oi = sum(r.pe.oi or 0 for r in chain.strikes if r.pe)
        if total_ce_oi > 0:
            pcr_val = total_pe_oi / total_ce_oi

    options_bias = "Positive" if pcr_val > 1.1 else ("Negative" if pcr_val < 0.85 else "Neutral")

    for news in items:
        aligned = (news.direction == options_bias) or (news.direction == "Mixed")
        status_label = "Confirmation" if aligned else "Divergence"
        
        analysis_text = (
            f"News indicates {news.direction.lower()} impact for {news.affected_asset}. "
            f"Options PCR ({round(pcr_val, 2)}) reflects {options_bias.lower()} positioning. "
            f"Data {'confirms headline narrative' if aligned else 'shows divergence with option chain pricing'}."
        )

        fusion_results.append(NewsFusionResult(
            news_id=news.id,
            headline=news.headline,
            news_bias=news.direction,
            options_pricing_bias=options_bias if options_bias in ["Positive", "Negative", "Neutral"] else "Neutral",
            aligned=aligned,
            status_label=status_label,
            analysis=analysis_text,
            confidence=news.confidence
        ))

    return NewsResponsePayload(
        timestamp=datetime.now(timezone.utc),
        status="ok" if items else "unavailable",
        categories=["RBI", "Budget", "Fed", "CPI", "Earnings", "FII_DII", "Geopolitical", "Crude_INR", "SEBI"],
        items=items,
        fusion_insights=fusion_results
    )
