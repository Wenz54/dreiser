"""Portfolio model - виртуальный портфель пользователя"""
from sqlalchemy import Column, ForeignKey, DECIMAL, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class Portfolio(BaseModel):
    """Virtual portfolio model (SIMULATED trading)"""
    
    __tablename__ = "portfolios"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Virtual balances (SIMULATION) - ЕДИНЫЙ баланс для SPOT + FUTURES
    balance_usd = Column(DECIMAL(20, 8), default=1000.00, nullable=False, comment="Total balance (spot + futures margin)")
    initial_balance = Column(DECIMAL(20, 8), default=1000.00, nullable=False, comment="Initial balance")
    total_pnl = Column(DECIMAL(20, 8), default=0.00, nullable=False, comment="Total P&L (spot + futures)")
    
    # Statistics (from simulation)
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="portfolio")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")  # Spot positions
    futures_positions = relationship("FuturesPosition", back_populates="portfolio", cascade="all, delete-orphan")  # Futures positions
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    ai_decisions = relationship("AIDecision", back_populates="portfolio", cascade="all, delete-orphan")
    ai_sessions = relationship("AITradingSession", back_populates="portfolio", cascade="all, delete-orphan")
    performance_score = relationship("PerformanceScore", back_populates="portfolio", uselist=False, cascade="all, delete-orphan")

