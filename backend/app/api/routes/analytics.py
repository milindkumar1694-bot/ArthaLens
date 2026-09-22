from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/{symbol}", summary="Deterministic options analytics; not trading advice")
async def analytics(symbol: str, request: Request, p_expiry: str | None = None, strike_range: int | None = Query(default=None, ge=0)):
    try:
        chain = await request.app.state.market_service.option_chain(symbol, p_expiry)
        return await request.app.state.analytics_service.calculate(chain, strike_range)
    except ValueError as error: raise HTTPException(status_code=404, detail=str(error)) from error
