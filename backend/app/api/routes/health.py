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

    checks = {
        "application": "CONNECTED",
        "data_mode": settings.data_mode.upper(),
        "market_provider": (settings.broker_provider or "UNCONFIGURED").upper(),
        "database_check": state.database_check(),
        "redis_check": state.cache.status,
        **readiness
    }

    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        checks=checks
    )
