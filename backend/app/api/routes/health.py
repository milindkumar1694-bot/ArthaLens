from fastapi import APIRouter, Request
from app.config.validator import validate_production_config
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse, summary="Production health and component readiness checks")
async def health(request: Request) -> HealthResponse:
    state = request.app.state
    settings = state.settings

    readiness = getattr(state, "config_readiness", None)
    if not readiness:
        readiness = validate_production_config(settings)

    db_status = state.database_check() if hasattr(state, "database_check") and callable(state.database_check) else "unavailable"
    redis_status = state.cache.status if hasattr(state, "cache") else "unavailable"

    # Evaluate broker live status without triggering re-authentication
    market_service = getattr(state, "market_service", None)
    broker_config = "COMPLETE" if settings.is_broker_configured else "INCOMPLETE"

    if settings.data_mode == "live":
        if market_service and market_service.provider:
            p_status = await market_service.provider_status()
            broker_auth = "SUCCESS" if p_status.connected else "FAILED"
            broker_conn = "AVAILABLE" if p_status.connected else "UNAVAILABLE"
            broker_msg = p_status.message or ("Angel One SmartAPI connected" if p_status.connected else "Angel One authentication failed or connection unavailable")
        else:
            broker_auth = "FAILED"
            broker_conn = "UNAVAILABLE"
            broker_msg = "Broker provider not initialized"
    else:
        broker_auth = "SUCCESS"
        broker_conn = "AVAILABLE"
        broker_msg = "Mock provider active"

    # Evaluate Redis live status
    is_redis_cfg = settings.is_redis_configured
    redis_cfg_status = "CONFIGURED" if is_redis_cfg else "NOT_CONFIGURED"
    if is_redis_cfg:
        redis_conn_status = "AVAILABLE" if redis_status == "ok" else "UNAVAILABLE"
    else:
        redis_conn_status = "NOT_CONFIGURED"

    checks = {
        "application": "CONNECTED",
        "data_mode": settings.data_mode.upper(),
        "market_provider": (settings.broker_provider or "UNCONFIGURED").upper(),
        "database_check": db_status,
        "redis_check": redis_status,
        "broker_configuration": broker_config,
        "broker_authentication": broker_auth,
        "broker_connectivity": broker_conn,
        "broker_message": broker_msg,
        "redis_configuration": redis_cfg_status,
        "redis_connectivity": redis_conn_status,
        **readiness
    }

    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        checks=checks
    )
