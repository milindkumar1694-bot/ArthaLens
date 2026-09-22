from fastapi import APIRouter, Request
from app.analytics.news_fusion import analyze_news_fusion
from app.schemas.news import NewsResponsePayload
from app.data.providers.news_provider import NewsProvider

router = APIRouter(prefix="/news", tags=["news"])

@router.get("", response_model=NewsResponsePayload, summary="Options-impacting news intelligence & fusion logic")
async def get_news_intelligence(request: Request, symbol: str = "NIFTY"):
    chain = None
    try:
        chain = await request.app.state.market_service.option_chain(symbol)
    except Exception:
        pass

    settings = request.app.state.settings
    is_live = (settings.data_mode == "live")

    live_news_items = None
    if is_live and settings.is_news_configured:
        provider = NewsProvider(settings)
        live_news_items = await provider.fetch_live_news(query=f"{symbol} OR RBI OR Indian stock market", limit=10)

    return analyze_news_fusion(chain, is_live_mode=is_live, live_news_items=live_news_items)
