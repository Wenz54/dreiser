"""Performance Log model - GPT мониторинг DeepSeek"""
from sqlalchemy import Column, ForeignKey, Integer, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class PerformanceLog(BaseModel):
    """
    Лог анализа работы DeepSeek от GPT Performance Monitor
    """
    
    __tablename__ = "performance_logs"
    
    # Relations
    ai_decision_id = Column(UUID(as_uuid=True), ForeignKey("ai_decisions.id", ondelete="CASCADE"), nullable=False)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    # GPT Analysis Scores (1-10)
    analysis_quality = Column(Integer, nullable=False, comment="Quality of market analysis (1-10)")
    decision_appropriateness = Column(Integer, nullable=False, comment="Was decision appropriate? (1-10)")
    risk_management = Column(Integer, nullable=False, comment="Risk management score (1-10)")
    overall_score = Column(Integer, nullable=False, comment="Overall performance score (1-10)")
    
    # Confidence Assessment
    confidence_assessment = Column(Text, nullable=True, comment="appropriate/overconfident/underconfident")
    
    # Feedback
    strengths = Column(JSONB, nullable=True, comment="Identified strengths")
    weaknesses = Column(JSONB, nullable=True, comment="Identified weaknesses")
    recommendations = Column(JSONB, nullable=True, comment="Recommendations for improvement")
    
    # Pattern Recognition
    pattern_identified = Column(Text, nullable=True, comment="Trading pattern identified")
    
    # Summary
    summary = Column(Text, nullable=True, comment="2-sentence assessment")
    
    # Outcome (if trade executed)
    outcome_pnl = Column(DECIMAL(20, 8), nullable=True, comment="Actual P&L if trade closed")
    outcome_duration_hours = Column(DECIMAL(10, 2), nullable=True, comment="Trade duration in hours")
    outcome_profitable = Column(Integer, nullable=True, comment="1=profitable, 0=loss, NULL=pending")
    
    # Full GPT response
    gpt_analysis = Column(JSONB, nullable=True, comment="Full GPT response")
    
    # Relationships
    ai_decision = relationship("AIDecision", backref="performance_logs")
    portfolio = relationship("Portfolio", backref="performance_logs")







