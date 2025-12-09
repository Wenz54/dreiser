"""AI Decision model - решения DeepSeek AI"""
from sqlalchemy import Column, ForeignKey, String, DECIMAL, Boolean, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.db.base import BaseModel


class DecisionType(str, enum.Enum):
    """AI decision types"""
    BUY = "BUY"              # Spot: купить актив
    SELL = "SELL"            # Spot: продать актив
    HOLD = "HOLD"            # Держать/ждать
    LONG = "LONG"            # Futures: ставка на рост (3x leverage)
    SHORT = "SHORT"          # Futures: ставка на падение (3x leverage)
    CLOSE_LONG = "CLOSE_LONG"    # Закрыть LONG futures позицию
    CLOSE_SHORT = "CLOSE_SHORT"  # Закрыть SHORT futures позицию
    WAIT = "WAIT"            # Ждать сигнала (синоним HOLD)


class AIDecision(BaseModel):
    """AI trading decision record"""
    
    __tablename__ = "ai_decisions"
    
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    decision_type = Column(String(20), nullable=False)  # Changed from SQLEnum to String to avoid PostgreSQL enum issues
    symbol = Column(String(20), nullable=False)
    confidence = Column(DECIMAL(5, 2), nullable=True, comment="AI confidence 0-100%")
    reasoning = Column(Text, nullable=True, comment="AI explanation")
    
    market_data = Column(JSONB, nullable=True, comment="Market snapshot at decision time")
    model_version = Column(String(50), nullable=True, comment="DeepSeek model version")
    processing_time_ms = Column(Integer, nullable=True, comment="AI processing time")
    
    executed = Column(Boolean, default=False, nullable=False, comment="Was decision executed?")
    
    # Trading parameters (from AI expectation)
    target_price = Column(DECIMAL(20, 8), nullable=True, comment="AI target price")
    stop_loss = Column(DECIMAL(20, 8), nullable=True, comment="AI stop loss price")
    time_horizon = Column(String(20), nullable=True, comment="Expected time horizon")
    sell_percentage = Column(Integer, default=100, nullable=False, comment="% to sell (100=all, 40-50=partial)")
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="ai_decisions")
    transaction = relationship("Transaction", back_populates="ai_decision", uselist=False)






