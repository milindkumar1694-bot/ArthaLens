from fastapi import APIRouter, Request

from app.config.validator import (
    validate_production_config,
)
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Production health and component readiness checks",
)
async def health(
    request: Request,
) -> HealthResponse:
    state = request.app.state
    settings = state.settings

    # Copy configuration state so one HTTP request cannot mutate
    # the application's original readiness dictionary.
    readiness = dict(
        getattr(
            state,
            "config_readiness",
            None,
        )
        or validate_production_config(settings)
    )

    market_service = getattr(
        state,
        "market_service",
        None,
    )

    # --------------------------------------------------------------
    # Database
    # --------------------------------------------------------------

    if (
        hasattr(state, "database_check")
        and callable(state.database_check)
    ):
        database_status = state.database_check()
    else:
        database_status = "unavailable"

    # --------------------------------------------------------------
    # Redis
    # --------------------------------------------------------------

    cache = getattr(
        state,
        "cache",
        None,
    )

    redis_status = (
        cache.status
        if cache is not None
        else "unavailable"
    )

    redis_configured = (
        settings.is_redis_configured
    )

    if not redis_configured:
        redis_configuration = "NOT_CONFIGURED"
        redis_connectivity = "NOT_CONFIGURED"
    else:
        redis_configuration = "CONFIGURED"
        redis_connectivity = (
            "AVAILABLE"
            if redis_status == "ok"
            else "UNAVAILABLE"
        )

    # --------------------------------------------------------------
    # Broker runtime state
    # --------------------------------------------------------------

    if market_service and market_service.provider:
        provider_status = (
            await market_service.provider_status()
        )

        broker_configuration = (
            "COMPLETE"
            if provider_status.configured
            else "INCOMPLETE"
        )

        if settings.data_mode == "live":
            broker_authentication = (
                "SUCCESS"
                if provider_status.connected
                else (
                    "FAILED"
                    if provider_status.configured
                    else "NOT_ATTEMPTED"
                )
            )

            broker_connectivity = (
                "AVAILABLE"
                if provider_status.connected
                else "UNAVAILABLE"
            )

            broker_message = (
                provider_status.message
                or (
                    "Angel One SmartAPI authenticated"
                    if provider_status.connected
                    else (
                        "Angel One authentication failed "
                        "or connection unavailable"
                    )
                )
            )

        else:
            broker_authentication = "MOCK_SIMULATION"
            broker_connectivity = "AVAILABLE"
            broker_message = "Mock provider active"

    else:
        broker_configuration = "INCOMPLETE"
        broker_authentication = "NOT_ATTEMPTED"
        broker_connectivity = "UNAVAILABLE"
        broker_message = (
            "Broker provider not initialized"
        )

    # --------------------------------------------------------------
    # IMPORTANT:
    # Runtime values overwrite configuration-only values.
    # Do NOT put **readiness at the end.
    # --------------------------------------------------------------

    checks = {
        **readiness,

        "application": "CONNECTED",
        "data_mode": settings.data_mode.upper(),
        "market_provider": (
            settings.broker_provider
            or "UNCONFIGURED"
        ).upper(),

        "database_check": database_status,

        "redis_check": redis_status,

        "broker_configuration": (
            settings.broker_configuration_status
        ),
        "broker_authentication": broker_authentication,
        "broker_connectivity": broker_connectivity,
        "broker_message": broker_message,

        "redis_configuration": redis_configuration,
        "redis_connectivity": redis_connectivity,

        "broker": (
            f"CONFIGURED "
            f"({settings.broker_provider.upper()})"
            if settings.is_broker_configured
            else (
                "UNCONFIGURED "
                f"({settings.broker_provider.upper()})"
            )
        ),
    }

    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        checks={
            str(key): str(value)
            for key, value in checks.items()
        },
    )
