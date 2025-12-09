"""Position model - виртуальная позиция"""
from sqlalchemy import Column, ForeignKey, String, DECIMAL, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class Position(BaseModel):
    """Virtual trading position (SIMULATED)"""
    
    __tablename__ = "positions"
    
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    symbol = Column(String(20), nullable=False, comment="Trading pair (e.g., BTCUSDT)")
    quantity = Column(DECIMAL(20, 8), nullable=False, comment="Virtual quantity held")
    entry_price = Column(DECIMAL(20, 8), nullable=False, comment="Average entry price (DCA)")
    current_price = Column(DECIMAL(20, 8), nullable=True, comment="Current market price")
    unrealized_pnl = Column(DECIMAL(20, 8), nullable=True, comment="Unrealized P&L")
    entry_volume_ratio = Column(DECIMAL(10, 2), nullable=True, comment="Volume ratio at entry (5m/avg_15m)")
    buy_count = Column(Integer, default=1, nullable=False, comment="Number of buy orders (DCA)")
    partial_sells = Column(Integer, default=0, nullable=False, comment="Number of partial sells")
    
    is_closed = Column(Boolean, default=False, nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False, comment="Flag: this is SIMULATION")
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    transactions = relationship("Transaction", back_populates="position")






