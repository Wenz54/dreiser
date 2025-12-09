"""Market data endpoints"""
from fastapi import APIRouter, HTTPException
from decimal import Decimal

from app.services.binance_service import binance_service


router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/price/{symbol}")
async def get_price(symbol: str = "BTCUSDT"):
    """
    Получить текущую цену с Binance
    
    Args:
        symbol: Trading pair (default: BTCUSDT)
    
    Returns:
        Current price
    """
    price = await binance_service.get_ticker_price(symbol)
    
    if not price:
        raise HTTPException(status_code=503, detail="Failed to fetch price from Binance")
    
    return {
        "symbol": symbol,
        "price": float(price),
        "source": "Binance",
        "is_simulated": False
    }


@router.get("/ticker/{symbol}")
async def get_24h_ticker(symbol: str = "BTCUSDT"):
    """
    Получить 24h статистику
    
    Returns:
        24h ticker data from Binance
    """
    ticker = await binance_service.get_24h_ticker(symbol)
    
    if not ticker:
        raise HTTPException(status_code=503, detail="Failed to fetch ticker from Binance")
    
    return {
        "symbol": ticker["symbol"],
        "price": float(ticker["price"]),
        "change_24h": float(ticker["change_24h"]),
        "high_24h": float(ticker["high_24h"]),
        "low_24h": float(ticker["low_24h"]),
        "volume_24h": float(ticker["volume_24h"]),
        "source": "Binance"
    }


@router.get("/candles/{symbol}")
async def get_candles(
    symbol: str = "BTCUSDT",
    interval: str = "15m",
    limit: int = 100
):
    """
    Получить свечи (OHLCV)
    
    Args:
        symbol: Trading pair
        interval: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of candles (max 1000)
    
    Returns:
        List of candles
    """
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 1000")
    
    candles = await binance_service.get_klines(symbol, interval, limit)
    
    if not candles:
        raise HTTPException(status_code=503, detail="Failed to fetch candles from Binance")
    
    return {
        "symbol": symbol,
        "interval": interval,
        "candles": [
            {
                "timestamp": candle["open_time"],
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
                "volume": float(candle["volume"])
            }
            for candle in candles
        ]
    }


@router.get("/orderbook/{symbol}")
async def get_orderbook(symbol: str = "BTCUSDT", depth: int = 10):
    """
    Получить order book
    
    Args:
        symbol: Trading pair
        depth: Depth (5, 10, 20)
    
    Returns:
        Order book data
    """
    if depth not in [5, 10, 20]:
        raise HTTPException(status_code=400, detail="Depth must be 5, 10, or 20")
    
    orderbook = await binance_service.get_order_book(symbol, depth)
    
    if not orderbook:
        raise HTTPException(status_code=503, detail="Failed to fetch order book from Binance")
    
    return {
        "symbol": symbol,
        "bids": [[float(price), float(qty)] for price, qty in orderbook["bids"]],
        "asks": [[float(price), float(qty)] for price, qty in orderbook["asks"]]
    }












