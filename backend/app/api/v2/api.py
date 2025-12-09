"""
DRAIZER V2 API Router
Combines all V2 endpoints
"""

from fastapi import APIRouter

from app.api.v2.endpoints import engine, arbitrage, operations

api_router_v2 = APIRouter()

api_router_v2.include_router(engine.router, prefix="/engine", tags=["engine"])
api_router_v2.include_router(arbitrage.router, prefix="/arbitrage", tags=["arbitrage"])
api_router_v2.include_router(operations.router, prefix="/operations", tags=["operations"])
# backtest.router временно отключен (requires pandas)

