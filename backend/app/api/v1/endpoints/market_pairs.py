"""Market pairs endpoint"""
from fastapi import APIRouter
from app.core.config import settings
from app.services.binance_service import binance_service


router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/pairs")
async def get_all_pairs():
    """Получить цены всех торговых пар"""
    pairs_data = []
    
    for symbol in settings.TRADING_PAIRS:
        try:
            price = await binance_service.get_ticker_price(symbol)
            ticker_24h = await binance_service.get_24h_ticker(symbol)
            
            if price and ticker_24h:
                pairs_data.append({
                    "symbol": symbol,
                    "price": float(price),
                    "change_24h": float(ticker_24h.get("change_24h", 0)),
                    "volume_24h": float(ticker_24h.get("volume_24h", 0)),
                    "high_24h": float(ticker_24h.get("high_24h", 0)),
                    "low_24h": float(ticker_24h.get("low_24h", 0))
                })
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            continue
    
    return {
        "pairs": pairs_data,
        "count": len(pairs_data)
    }





