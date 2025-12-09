"""
API V2 - Quantitative Arbitrage Bot
"""

from fastapi import APIRouter
from app.api.v2.endpoints import engine, arbitrage, operations, backtest

api_router = APIRouter()

# Include all V2 endpoints
api_router.include_router(engine.router, prefix="/engine", tags=["engine"])
api_router.include_router(arbitrage.router, prefix="/arbitrage", tags=["arbitrage"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
