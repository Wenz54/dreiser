"""API v1 router aggregator"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, portfolio, trading, market, market_pairs


api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(portfolio.router)
api_router.include_router(trading.router)
api_router.include_router(market.router)
api_router.include_router(market_pairs.router)  # Multiple trading pairs

