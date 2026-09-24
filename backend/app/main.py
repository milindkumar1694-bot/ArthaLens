import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.analytics import AnalyticsService
from app.api.routes import (
    analytics,
    expiry,
    health,
    market,
    news,
    options,
    watchlist,
)
from app.config import get_settings
from app.config.validator import validate_production_config
from app.database.session import (
    create_database_engine,
    database_check,
)
from app.logging import configure_logging
from app.services.cache import Cache
from app.services.llm import LLMService
from app.services.market import MarketDataService
from app.services.telegram_alert import TelegramAlertService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    settings = get_settings()

    logger.info(
        "ArthaLens startup initiated "
        "env=%s data_mode=%s provider=%s",
        settings.app_env,
        settings.data_mode,
        settings.provider_name or "unconfigured",
    )

    config_readiness = validate_production_config(
        settings
    )

    app.state.settings = settings
    app.state.config_readiness = config_readiness

    engine = create_database_engine(
        settings.database_url
    )

    cache = Cache(
        settings.redis_url
    )

    await cache.connect()

    app.state.cache = cache
    app.state.database_check = (
        lambda: database_check(engine)
    )

    # IMPORTANT:
    # Create exactly one MarketDataService/provider instance
    # and retain it for the complete application lifecycle.
    app.state.market_service = MarketDataService(
        settings,
        cache,
    )

    app.state.analytics_service = AnalyticsService(
        settings,
        cache,
    )

    app.state.telegram_service = (
        TelegramAlertService(settings)
    )

    app.state.llm_service = LLMService(
        settings
    )

    # --------------------------------------------------------------
    # Authenticate the SAME provider instance used by all routes.
    # --------------------------------------------------------------

    provider_before_connect = (
        await app.state.market_service.provider_status()
    )

    logger.info(
        "Provider initialized "
        "provider=%s configured=%s connected=%s",
        provider_before_connect.provider,
        provider_before_connect.configured,
        provider_before_connect.connected,
    )

    provider_after_connect = (
        await app.state.market_service.connect()
    )

    logger.info(
        "Provider authentication result "
        "provider=%s configured=%s connected=%s "
        "status=%s message=%s",
        provider_after_connect.provider,
        provider_after_connect.configured,
        provider_after_connect.connected,
        provider_after_connect.status,
        provider_after_connect.message or "",
    )

    logger.info(
        "ArthaLens dependencies status "
        "database=%s redis=%s",
        app.state.database_check(),
        cache.status,
    )

    logger.info(
        "ArthaLens API started "
        "environment=%s data_mode=%s provider=%s",
        settings.app_env,
        settings.data_mode,
        provider_after_connect.provider,
    )

    scheduler = AsyncIOScheduler()

    async def refresh_markets():
        for symbol in (
            "NIFTY",
            "BANKNIFTY",
            "SENSEX",
            "INDIAVIX",
        ):
            try:
                result = (
                    await app.state.market_service.quote(
                        symbol
                    )
                )

                logger.debug(
                    "Market refresh "
                    "symbol=%s status=%s",
                    symbol,
                    result.status,
                )

            except Exception as exc:
                logger.exception(
                    "Market refresh failed "
                    "symbol=%s error=%s",
                    symbol,
                    exc,
                )

    async def refresh_options():
        for symbol in (
            "NIFTY",
            "BANKNIFTY",
        ):
            try:
                result = (
                    await app.state.market_service.option_chain(
                        symbol
                    )
                )

                logger.debug(
                    "Option refresh "
                    "symbol=%s status=%s",
                    symbol,
                    result.status,
                )

            except Exception as exc:
                logger.exception(
                    "Option-chain refresh failed "
                    "symbol=%s error=%s",
                    symbol,
                    exc,
                )

    async def refresh_expiries():
        for symbol in (
            "NIFTY",
            "BANKNIFTY",
        ):
            try:
                result = (
                    await app.state.market_service.expiries(
                        symbol
                    )
                )

                logger.debug(
                    "Expiry refresh "
                    "symbol=%s status=%s",
                    symbol,
                    result.status,
                )

            except Exception as exc:
                logger.exception(
                    "Expiry refresh failed "
                    "symbol=%s error=%s",
                    symbol,
                    exc,
                )

    scheduler.add_job(
        refresh_markets,
        "interval",
        seconds=settings.market_refresh_seconds,
        id="market_refresh",
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        refresh_options,
        "interval",
        seconds=settings.option_chain_refresh_seconds,
        id="option_chain_refresh",
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        refresh_expiries,
        "interval",
        seconds=settings.expiry_refresh_seconds,
        id="expiry_refresh",
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    app.state.scheduler = scheduler

    logger.info(
        "Scheduler started "
        "market=%ss option_chain=%ss expiry=%ss",
        settings.market_refresh_seconds,
        settings.option_chain_refresh_seconds,
        settings.expiry_refresh_seconds,
    )

    try:
        yield
    finally:
        scheduler.shutdown(
            wait=False
        )

        await app.state.market_service.disconnect()

        await cache.close()

        if engine is not None:
            engine.dispose()

        logger.info(
            "ArthaLens API shutdown"
        )


settings = get_settings()

app = FastAPI(
    title="ArthaLens",
    version="0.1.0",
    description=(
        "Live market-intelligence foundation. "
        "Not investment advice."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(
        settings.cors_origins
    ),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(
    health.router,
    prefix=settings.api_prefix,
)

app.include_router(
    market.router,
    prefix=settings.api_prefix,
)

app.include_router(
    options.router,
    prefix=settings.api_prefix,
)

app.include_router(
    analytics.router,
    prefix=settings.api_prefix,
)

app.include_router(
    expiry.router,
    prefix=settings.api_prefix,
)

app.include_router(
    news.router,
    prefix=settings.api_prefix,
)

app.include_router(
    watchlist.router,
    prefix=settings.api_prefix,
)


@app.exception_handler(Exception)
async def unexpected_error(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled request error path=%s",
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": (
                    "An unexpected service error occurred."
                ),
            }
        },
    )
