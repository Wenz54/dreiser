"""Portfolio schemas"""
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
import uuid


class PortfolioBase(BaseModel):
    """Base portfolio schema"""
    balance_usd: Decimal = Field(..., ge=0)
    total_pnl: Decimal = Field(default=Decimal("0.00"))


class PortfolioResponse(PortfolioBase):
    """Portfolio response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    initial_balance: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PortfolioStats(BaseModel):
    """Portfolio statistics"""
    balance_usd: Decimal
    total_pnl: Decimal
    total_pnl_percent: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    best_trade: Decimal
    worst_trade: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    
    class Config:
        from_attributes = True












