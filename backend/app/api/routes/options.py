from fastapi import APIRouter, HTTPException, Query, Request
from app.schemas.options import ExpiryInfo, OptionChain

router = APIRouter(prefix="/options", tags=["options"])

@router.get("/expiries", response_model=ExpiryInfo, summary="Discover option expiries for an underlying")
async def get_expiries(request: Request, symbol: str = Query(...)) -> ExpiryInfo:
    try: return await request.app.state.market_service.expiries(symbol)
    except ValueError as error: raise HTTPException(status_code=404, detail=str(error)) from error

@router.get("/{symbol}", response_model=OptionChain, summary="Normalized option chain without analytics")
async def get_option_chain(symbol: str, request: Request, expiry: str | None = None, strike_range: int | None = Query(default=None, ge=0)) -> OptionChain:
    try: return await request.app.state.market_service.option_chain(symbol, expiry, strike_range)
    except ValueError as error: raise HTTPException(status_code=404, detail=str(error)) from error
