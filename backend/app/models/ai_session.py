"""AI Trading Session model"""
from sqlalchemy import Column, ForeignKey, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.db.base import BaseModel


class AITradingSession(BaseModel):
    """Активная AI торговая сессия"""
    
    __tablename__ = "ai_trading_sessions"
    
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ends_at = Column(DateTime, nullable=False)  # Когда сессия должна закончиться
    stopped_at = Column(DateTime, nullable=True)  # Когда была остановлена вручную
    
    total_analyses = Column(Integer, default=0, comment="Количество выполненных анализов")
    total_trades = Column(Integer, default=0, comment="Количество сделок за сессию")
    observation_mode_until = Column(DateTime, nullable=True, comment="Режим наблюдения до этого времени (10 минут)")
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="ai_sessions")
    
    def is_expired(self) -> bool:
        """Проверить истекла ли сессия"""
        return datetime.utcnow() >= self.ends_at
    
    def get_remaining_minutes(self) -> int:
        """Получить оставшееся время в минутах"""
        if not self.is_active:
            return 0
        remaining = self.ends_at - datetime.utcnow()
        return max(0, int(remaining.total_seconds() / 60))

