"""
DRAIZER V2 - Trading Service Stub
Minimal stub for V1 API compatibility
"""
from sqlalchemy.ext.asyncio import AsyncSession


class TradingService:
    """
    Trading service stub (V2 uses C engine instead)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_portfolio_stats(self, portfolio_id: str):
        """Get portfolio statistics"""
        return {
            "message": "V2 uses C engine for trading"
        }


