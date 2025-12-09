"""AI Learning Notes model - AI's self-improvement journal"""
import uuid
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DECIMAL, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

from app.db.base import BaseModel


class AILearningNote(BaseModel):
    """
    AI Learning Note - AI's post-mortem analysis of each trade
    
    AI анализирует каждую закрытую сделку и делает заметки:
    - Что сработало хорошо (в прибыльных сделках)
    - Что пошло не так (в убыточных сделках)
    - Урок, который AI извлек
    """
    
    __tablename__ = "ai_learning_notes"
    
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("ai_decisions.id", ondelete="SET NULL"), nullable=True)
    
    # Trade details
    symbol = Column(String(20), nullable=False)
    position_type = Column(String(10), nullable=False, comment="SPOT, LONG, or SHORT")  # КРИТИЧНО!
    trade_result = Column(String(10), nullable=False, comment="WIN or LOSS")  # КРИТИЧНО!
    profit_loss = Column(DECIMAL(20, 8), nullable=False, comment="Profit/Loss in USD (main field)")
    entry_price = Column(DECIMAL(20, 8), nullable=True)
    exit_price = Column(DECIMAL(20, 8), nullable=True)
    pnl = Column(DECIMAL(20, 8), nullable=True, comment="Profit/Loss in USD (legacy)")
    pnl_percent = Column(DECIMAL(10, 4), nullable=True, comment="P&L percentage")
    duration_minutes = Column(Integer, nullable=True, comment="Trade duration in minutes")
    
    # AI's analysis
    was_profitable = Column(Boolean, nullable=False)
    what_went_right = Column(Text, nullable=True, comment="What worked well (AI analysis)")
    what_went_wrong = Column(Text, nullable=True, comment="What went wrong (AI analysis)")
    lesson_learned = Column(Text, nullable=False, comment="Key lesson learned")
    improvement_suggestion = Column(Text, nullable=True, comment="How to improve next time")
    
    # Context
    market_conditions = Column(JSONB, nullable=True, comment="Market context at trade time")
    news_context = Column(Text, nullable=True, comment="News context during trade")
    
    # Metadata
    ai_confidence_at_entry = Column(DECIMAL(5, 2), nullable=True)
    ai_reasoning_at_entry = Column(Text, nullable=True)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AILearningNote {self.symbol} P&L:{self.pnl_percent:.2f}% - {self.lesson_learned[:50]}>"

