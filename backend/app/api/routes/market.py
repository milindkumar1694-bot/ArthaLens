from fastapi import APIRouter, HTTPException, Request
from app.schemas.market import MarketSnapshot

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/{symbol}", response_model=MarketSnapshot, summary="Normalized market snapshot")
async def get_market(symbol: str, request: Request) -> MarketSnapshot:
    try: return await request.app.state.market_service.quote(symbol)
    except ValueError as error: raise HTTPException(status_code=404, detail=str(error)) from error
