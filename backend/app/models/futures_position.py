"""Futures Position model - фьючерсные позиции с leverage"""
from sqlalchemy import Column, ForeignKey, String, DECIMAL, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from app.db.base import BaseModel


class FuturesPosition(BaseModel):
    """
    Futures position model (VIRTUAL, 3x leverage)
    
    LONG: Profit when price goes UP
    SHORT: Profit when price goes DOWN
    """
    
    __tablename__ = "futures_positions"
    
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False, comment="e.g. BTCUSDT")
    
    # Position type
    side = Column(String(10), nullable=False, comment="LONG or SHORT")
    
    # Position details
    entry_price = Column(DECIMAL(20, 8), nullable=False, comment="Entry price")
    quantity = Column(DECIMAL(20, 8), nullable=False, comment="Position size (in asset)")
    leverage = Column(Integer, default=3, nullable=False, comment="Leverage (default 3x)")
    entry_volume_ratio = Column(DECIMAL(10, 2), nullable=True, comment="Volume ratio at entry (5m/avg_15m)")
    
    # Current state
    current_price = Column(DECIMAL(20, 8), nullable=True, comment="Last known price")
    unrealized_pnl = Column(DECIMAL(20, 8), default=Decimal("0"), comment="Current P&L")
    liquidation_price = Column(DECIMAL(20, 8), nullable=True, comment="Price at which position liquidates")
    
    # Closure
    is_closed = Column(Boolean, default=False, nullable=False)
    exit_price = Column(DECIMAL(20, 8), nullable=True, comment="Exit price when closed")
    realized_pnl = Column(DECIMAL(20, 8), nullable=True, comment="Final P&L when closed")
    closed_at = Column(DateTime, nullable=True)
    
    # Simulation flag
    is_simulated = Column(Boolean, default=True, nullable=False, comment="Virtual position")
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="futures_positions")
    
    def calculate_pnl(self, current_price: Decimal) -> Decimal:
        """
        Calculate P&L for futures position
        
        LONG: profit when price UP
        SHORT: profit when price DOWN
        
        NOTE: Leverage is already accounted in quantity!
        When opening: quantity = (margin * leverage) / entry_price
        So P&L = price_change * quantity (leverage already applied)
        """
        price_change = current_price - self.entry_price
        
        if self.side == "LONG":
            # LONG: profit when price rises
            pnl = price_change * self.quantity
        else:  # SHORT
            # SHORT: profit when price falls
            pnl = -price_change * self.quantity
        
        # NO need to multiply by leverage again - it's already in quantity!
        
        return pnl
    
    def calculate_liquidation_price(self) -> Decimal:
        """
        Calculate liquidation price
        
        Liquidation happens when loss = (margin / leverage)
        With 3x leverage: liquidation at ~33% loss from entry
        """
        liquidation_pct = Decimal("0.33")  # 33% loss = liquidation
        
        if self.side == "LONG":
            # LONG liquidates when price drops 33%
            liq_price = self.entry_price * (Decimal("1") - liquidation_pct)
        else:  # SHORT
            # SHORT liquidates when price rises 33%
            liq_price = self.entry_price * (Decimal("1") + liquidation_pct)
        
        return liq_price

