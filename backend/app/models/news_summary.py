"""News Summary model - для Telegram новостей"""
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import BigInteger

from app.db.base import Base


class NewsSummary(Base):
    """Telegram news summaries для DeepSeek контекста"""
    
    __tablename__ = "news_summaries"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Telegram source info
    channel_id = Column(String(100), nullable=False, comment="Telegram channel ID")
    channel_name = Column(String(255), nullable=True)
    
    # News data
    messages_count = Column(Integer, default=0, comment="Number of messages processed")
    raw_news = Column(JSONB, nullable=True, comment="Raw Telegram messages")
    
    # GPT-4 analysis
    gpt_summary = Column(Text, nullable=False, comment="GPT-4 dry facts summary for DeepSeek")
    keywords = Column(JSONB, nullable=True, comment="Extracted keywords")
    sentiment = Column(String(20), nullable=True, comment="Overall sentiment: bullish/bearish/neutral")
    
    # NEW: Relevance scoring
    overall_relevance = Column(Integer, default=0, comment="Overall relevance score 0-100")
    filtered_summary = Column(Text, nullable=True, comment="Filtered summary (only relevant news)")
    relevance_data = Column(JSONB, nullable=True, comment="Detailed relevance scoring per news")
    
    # Metadata
    processed_at = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False, comment="News period start")
    end_time = Column(DateTime, nullable=False, comment="News period end")
    
    # Status
    used_in_trading = Column(Boolean, default=False, comment="Was this summary used in DeepSeek decision?")
    
    # Security
    is_encrypted = Column(Boolean, default=False, comment="Is raw_news encrypted?")

