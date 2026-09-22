import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import analytics, health, market, options, expiry, news, watchlist
from app.config import get_settings
from app.database.session import create_database_engine, database_check
from app.logging import configure_logging
from app.services.market import MarketDataService
from app.services.cache import Cache
from app.services.telegram_alert import TelegramAlertService
from app.services.llm import LLMService
from app.analytics import AnalyticsService
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config.validator import validate_production_config

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(); settings = get_settings()
    config_readiness = validate_production_config(settings)
    app.state.settings = settings; app.state.config_readiness = config_readiness
    engine = create_database_engine(settings.database_url); cache = Cache(settings.redis_url); await cache.connect()
    app.state.cache = cache; app.state.database_check = lambda: database_check(engine); app.state.market_service = MarketDataService(settings, cache)
    app.state.analytics_service = AnalyticsService(settings, cache)
    app.state.telegram_service = TelegramAlertService(settings)
    app.state.llm_service = LLMService(settings)
    provider = await app.state.market_service.provider_status()
    logger.info("ArthaLens API started environment=%s data_mode=%s provider=%s database=%s redis=%s", settings.app_env, settings.data_mode, provider.provider, app.state.database_check(), "configured" if settings.redis_url else "not_configured")
    scheduler = AsyncIOScheduler()
    async def refresh_markets():
        for symbol in ("NIFTY", "BANKNIFTY", "SENSEX", "INDIAVIX"): await app.state.market_service.quote(symbol)
    async def refresh_options():
        for symbol in ("NIFTY", "BANKNIFTY"): await app.state.market_service.option_chain(symbol)
    async def refresh_expiries():
        for symbol in ("NIFTY", "BANKNIFTY"): await app.state.market_service.expiries(symbol)
    scheduler.add_job(refresh_markets, "interval", seconds=settings.market_refresh_seconds, id="market_refresh")
    scheduler.add_job(refresh_options, "interval", seconds=settings.option_chain_refresh_seconds, id="option_chain_refresh")
    scheduler.add_job(refresh_expiries, "interval", seconds=settings.expiry_refresh_seconds, id="expiry_refresh")
    scheduler.start(); app.state.scheduler = scheduler
    yield
    scheduler.shutdown(wait=False); await cache.close()
    logger.info("ArthaLens API shutdown")

settings = get_settings()
app = FastAPI(title="ArthaLens", version="0.1.0", description="Market-data foundation. Not investment advice.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False, allow_methods=["GET"], allow_headers=["*"])
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(market.router, prefix=settings.api_prefix)
app.include_router(options.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)
app.include_router(expiry.router, prefix=settings.api_prefix)
app.include_router(news.router, prefix=settings.api_prefix)
app.include_router(watchlist.router, prefix=settings.api_prefix)

@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled request error path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected service error occurred."}})
