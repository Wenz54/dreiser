"""Market data cache model"""
from sqlalchemy import Column, String, DECIMAL, DateTime, Index
from sqlalchemy import BigInteger

from app.db.base import Base


class MarketDataCache(Base):
    """Market data cache (from Binance)"""
    
    __tablename__ = "market_data_cache"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    symbol = Column(String(20), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=False)
    volume_24h = Column(DECIMAL(20, 8), nullable=True)
    change_24h = Column(DECIMAL(10, 4), nullable=True)
    high_24h = Column(DECIMAL(20, 8), nullable=True)
    low_24h = Column(DECIMAL(20, 8), nullable=True)
    
    timestamp = Column(DateTime, nullable=False)
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )












