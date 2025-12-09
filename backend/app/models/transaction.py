"""Transaction model - виртуальные сделки"""
from sqlalchemy import Column, ForeignKey, String, DECIMAL, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.db.base import BaseModel


class TransactionType(str, enum.Enum):
    """Transaction types"""
    BUY = "BUY"
    SELL = "SELL"
    LONG = "LONG"    # Futures long (open)
    SHORT = "SHORT"  # Futures short (open)
    CLOSE_LONG = "CLOSE_LONG"    # Futures long (close)
    CLOSE_SHORT = "CLOSE_SHORT"  # Futures short (close)


class Transaction(BaseModel):
    """Virtual transaction record (SIMULATED trade)"""
    
    __tablename__ = "transactions"
    
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    position_id = Column(UUID(as_uuid=True), ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    ai_decision_id = Column(UUID(as_uuid=True), ForeignKey("ai_decisions.id", ondelete="SET NULL"), nullable=True)
    
    type = Column(String(4), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False, comment="Virtual quantity traded")
    price = Column(DECIMAL(20, 8), nullable=False, comment="Execution price (real market price)")
    total_value = Column(DECIMAL(20, 8), nullable=False, comment="Total value in USD")
    
    fee = Column(DECIMAL(20, 8), default=0, comment="Platform fee (from virtual profits)")
    pnl = Column(DECIMAL(20, 8), nullable=True, comment="Profit/Loss (only for SELL)")
    
    is_simulated = Column(Boolean, default=True, nullable=False, comment="Flag: this is SIMULATION")
    simulated_price = Column(DECIMAL(20, 8), nullable=True, comment="Real Binance price used")
    
    extra_metadata = Column(JSONB, nullable=True, comment="Additional data")
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    position = relationship("Position", back_populates="transactions")
    ai_decision = relationship("AIDecision", back_populates="transaction")

