"""DeepSeek Context model - сжатие истории"""
from sqlalchemy import Column, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.db.base import BaseModel


class DeepSeekContext(BaseModel):
    """Сжатый контекст для DeepSeek (после каждых 10 операций)"""
    
    __tablename__ = "deepseek_contexts"
    
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    # Context summary
    summary = Column(Text, nullable=False, comment="GPT-4 summary of last 10 decisions")
    decisions_count = Column(Integer, default=10, comment="Number of decisions summarized")
    
    # Performance snapshot
    performance_snapshot = Column(JSONB, nullable=True, comment="Portfolio stats at this point")
    key_patterns = Column(JSONB, nullable=True, comment="Identified trading patterns")
    
    # Context window
    start_decision_id = Column(UUID(as_uuid=True), nullable=True, comment="First decision in this context")
    end_decision_id = Column(UUID(as_uuid=True), nullable=True, comment="Last decision in this context")
    
    # Metadata
    compressed_at = Column(DateTime, nullable=False)
    tokens_saved = Column(Integer, default=0, comment="Estimated tokens saved by compression")
    
    # Relationships
    portfolio = relationship("Portfolio", backref="deepseek_contexts")







