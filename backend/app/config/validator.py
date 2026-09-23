import logging
from app.config.settings import Settings

logger = logging.getLogger("arthalens.config")

def validate_production_config(settings: Settings) -> dict[str, str]:
    """Validates configuration readiness for live operational status without exposing secret values."""
    status = {}

    if settings.data_mode == "live":
        logger.info("Initializing ArthaLens in LIVE PRODUCTION DATA MODE (DATA_MODE=live)...")

        # Validate selected broker
        if not settings.broker_provider:
            status["broker"] = "UNCONFIGURED (BROKER_PROVIDER empty)"
            status["broker_configuration"] = "MISSING_PROVIDER"
            status["broker_authentication"] = "NOT_ATTEMPTED"
            logger.warning("Configuration Notice: BROKER_PROVIDER is empty. Live market endpoints will return status='unavailable'.")
        elif not settings.is_broker_configured:
            status["broker"] = f"UNCONFIGURED ({settings.broker_provider.upper()} keys missing)"
            status["broker_configuration"] = settings.broker_configuration_status
            status["broker_authentication"] = "NOT_ATTEMPTED"
            logger.warning("Configuration Notice: Live broker '%s' credentials are missing. Live market endpoints will return status='unavailable'.", settings.broker_provider)
        else:
            status["broker"] = f"CONFIGURED ({settings.broker_provider.upper()})"
            status["broker_configuration"] = settings.broker_configuration_status
            status["broker_authentication"] = "NOT_ATTEMPTED"
            logger.info("Broker Integration: Live broker '%s' credentials configured.", settings.broker_provider)

        # Validate news feed
        if not settings.is_news_configured:
            status["news"] = "UNCONFIGURED (NEWS_API_KEY missing)"
            logger.warning("Configuration Notice: NEWS_API_KEY is missing. Live news endpoints will return status='unavailable'.")
        else:
            status["news"] = f"CONFIGURED ({settings.news_provider.upper()})"

        # Validate database
        if not settings.is_database_configured:
            status["database"] = "UNCONFIGURED (DATABASE_URL missing)"
            logger.warning("Configuration Notice: DATABASE_URL is missing. Historical IV percentile will return status='unavailable'.")
        else:
            status["database"] = "CONFIGURED"

        # Validate Redis
        if not settings.is_redis_configured:
            status["redis"] = "UNCONFIGURED (Using in-process fallback)"
            status["redis_configuration"] = "UNCONFIGURED"
        else:
            status["redis"] = "CONFIGURED"
            status["redis_configuration"] = "CONFIGURED"

        # Validate Telegram
        if not settings.is_telegram_configured:
            status["telegram"] = "UNCONFIGURED (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing)"
        else:
            status["telegram"] = "CONFIGURED"

        # Validate LLM Provider
        provider = settings.llm_provider.lower().strip()
        if not settings.is_llm_configured:
            if provider == "xai":
                status["llm"] = "UNCONFIGURED (XAI_API_KEY missing)"
                logger.warning("Configuration Notice: XAI_API_KEY is missing. Grok LLM features will return status='unavailable'.")
            elif provider == "openai":
                status["llm"] = "UNCONFIGURED (OPENAI_API_KEY missing)"
                logger.warning("Configuration Notice: OPENAI_API_KEY is missing. OpenAI LLM features will return status='unavailable'.")
            else:
                status["llm"] = f"UNCONFIGURED (Unsupported LLM_PROVIDER '{settings.llm_provider}')"
                logger.warning("Configuration Notice: LLM_PROVIDER '%s' is not supported.", settings.llm_provider)
        else:
            status["llm"] = f"CONFIGURED ({provider.upper()})"
            logger.info("LLM Integration: Active provider '%s' configured with model '%s'.", provider, settings.active_llm_model)

    else:
        logger.info("Initializing ArthaLens in DEVELOPMENT SIMULATION MODE (DATA_MODE=mock).")
        status = {
            "broker": "MOCK_SIMULATION",
            "broker_configuration": "MOCK_SIMULATION",
            "broker_authentication": "MOCK_SIMULATION",
            "news": "MOCK_SIMULATION",
            "database": "MOCK_SIMULATION" if not settings.is_database_configured else "CONFIGURED",
            "redis": "IN_PROCESS" if not settings.is_redis_configured else "CONFIGURED",
            "redis_configuration": "IN_PROCESS" if not settings.is_redis_configured else "CONFIGURED",
            "telegram": "MOCK_LOGGING",
            "llm": "MOCK_SIMULATION"
        }

    return status
