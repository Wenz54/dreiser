"""Performance Score model - рейтинг AI трейдера"""
from sqlalchemy import Column, ForeignKey, Integer, DECIMAL, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import BaseModel


class PerformanceScore(BaseModel):
    """Рейтинг производительности AI трейдера (0-100)"""
    
    __tablename__ = "performance_scores"
    
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Рейтинг (0-100, старт с 50)
    score = Column(Integer, default=50, nullable=False, comment="AI performance rating (0-100)")
    
    # Статистика для расчета
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    total_pnl = Column(DECIMAL(20, 8), default=0, nullable=False)
    
    # Штрафы
    rule_violations = Column(Integer, default=0, nullable=False, comment="Игнорирование правил/уроков")
    
    # История изменений (последние)
    last_change_reason = Column(Text, nullable=True, comment="Причина последнего изменения")
    
    # Tracking для штрафа за простой
    last_trade_at = Column(DateTime, nullable=True, comment="Время последней сделки")
    last_inactivity_check_at = Column(DateTime, nullable=True, comment="Время последней проверки простоя")
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="performance_score")



